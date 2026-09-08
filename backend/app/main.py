import os
import shutil
import time
import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .config import UPLOADS_DIR, STARTER_DATA_DIR, SIMILARITY_THRESHOLD, MAX_CANDIDATES, GEMINI_API_KEY, OPENAI_API_KEY
from .models import (
    Fact, Evidence, Verdict, DocumentMetadata, FactDossier, IngestResponse,
    VerdictType, FactStatus
)
from .database import Database, get_doc_id
from .pdf_parser import PDFParser
from .embeddings import EmbeddingIndex, build_fact_text
from .llm_client import LLMClient
from .detective import DetectiveAgent
from .courtroom import CourtroomAgent
from .showcase import get_curated_showcase_exhibits, seed_showcase_data

app = FastAPI(title="The Fact Detective Agency", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
embedding_index = EmbeddingIndex(similarity_threshold=SIMILARITY_THRESHOLD)
llm_client = LLMClient()
detective = DetectiveAgent(llm_client)
courtroom = CourtroomAgent(llm_client)

# Seed showcase & load existing embeddings into index on startup
@app.on_event("startup")
def startup_event():
    existing_facts = db.get_facts()
    if not existing_facts:
        seed_showcase_data(db, embedding_index)
    else:
        saved_embeddings = db.load_all_embeddings()
        for f in existing_facts:
            vec = saved_embeddings.get(f.id)
            meta = {"doc_id": f.doc_id, "status": f.status.value}
            text = build_fact_text(f.subject, f.predicate, f.object, f.qualifiers)
            embedding_index.add_fact(f.id, text, meta, vector=vec)

# ----------------- INGESTION PIPELINE -----------------

def process_pdf_ingestion(filepath: Path, filename: str, max_pages: int = 25) -> IngestResponse:
    start_time = time.time()
    initial_llm_calls = getattr(llm_client, "call_count", 0)
    execution_log: List[str] = []

    parser = PDFParser(filepath)
    doc_id = get_doc_id(filename)
    total_pages = parser.get_page_count()
    execution_log.append(f"📄 Loaded PDF: '{filename}' ({total_pages} total pages detected).")

    doc_meta = DocumentMetadata(
        id=doc_id,
        filename=filename,
        filepath=str(filepath),
        total_pages=total_pages
    )
    db.add_document(doc_meta)

    pages = parser.extract_document_pages(max_pages=max_pages)
    execution_log.append(f"🔍 Interrogating first {len(pages)} pages for atomic claim extraction...")
    facts_extracted = 0
    adjudications_count = 0
    verdict_summary: Dict[str, int] = {
        VerdictType.CORROBORATED.value: 0,
        VerdictType.CONTRADICTED.value: 0,
        VerdictType.RECONCILED.value: 0,
        VerdictType.HUNG_JURY.value: 0,
        VerdictType.SUPERSEDED_BY.value: 0
    }

    for page_data in pages:
        p_num = page_data["page_number"]
        p_text = page_data["raw_text"]
        if not p_text.strip():
            continue

        # 1. Detective extracts atomic facts
        page_facts = detective.extract_facts_from_page(doc_id, filename, p_num, p_text)
        if page_facts:
            mode_badge = "Frontier LLM" if page_facts[0].extraction_method == "frontier_llm" else "Heuristic"
            execution_log.append(f"✨ Page {p_num}: Extracted {len(page_facts)} atomic claims [{mode_badge}].")
        
        for fact in page_facts:
            # Check character span accuracy with pdf_parser
            span_match = parser.find_text_span(fact.evidence.exact_text_span, page_hint=p_num)
            if span_match["found"]:
                fact.evidence.char_start = span_match["char_start"]
                fact.evidence.char_end = span_match["char_end"]
                fact.evidence.page_number = span_match["page"]

            db.add_fact(fact)
            facts_extracted += 1

            # 2. Add to embedding index
            fact_text = build_fact_text(fact.subject, fact.predicate, fact.object, fact.qualifiers)
            fact_vec = embedding_index.add_fact(fact.id, fact_text, {"doc_id": doc_id})
            db.save_embedding(fact.id, fact_vec.tolist())

            # 3. Courtroom Candidate Retrieval (Fast O(K) embedding search)
            candidates = embedding_index.search_candidates(
                fact_text,
                top_k=MAX_CANDIDATES,
                exclude_fact_id=fact.id
            )

            # 4. Adjudicate candidate pairs
            for cand in candidates:
                existing_fact = db.get_fact_by_id(cand["fact_id"])
                if not existing_fact or existing_fact.doc_id == fact.doc_id:
                    continue

                verdict = courtroom.adjudicate_pair(existing_fact, fact, similarity_score=cand["similarity"])
                db.add_verdict(verdict)
                adjudications_count += 1
                verdict_summary[verdict.verdict_type.value] = verdict_summary.get(verdict.verdict_type.value, 0) + 1
                execution_log.append(f"⚖️ Courtroom Verdict [{verdict.verdict_type.value}]: '{fact.subject}' (cos: {cand['similarity']:.2f})")

                # Lifecycle: update superseded fact status and backward/forward links
                if verdict.is_superseded and verdict.superseded_fact_id:
                    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    db.update_fact_status(
                        verdict.superseded_fact_id,
                        FactStatus.SUPERSEDED,
                        superseded_by=fact.id,
                        superseded_at=now_iso
                    )
                    fact.supersedes_fact_id = verdict.superseded_fact_id
                    db.add_fact(fact)
                    execution_log.append(f"🔄 Superseded older claim #{verdict.superseded_fact_id} with newly ingested claim #{fact.id}.")

    parser.close()

    elapsed = round(time.time() - start_time, 2)
    llm_calls_made = getattr(llm_client, "call_count", 0) - initial_llm_calls
    mode_str = "frontier_llm" if (llm_client.is_active() and llm_calls_made > 0) else "heuristic_fallback"
    execution_log.append(f"🏁 Completed in {elapsed}s: {facts_extracted} facts indexed, {adjudications_count} adjudications ({llm_calls_made} LLM calls).")

    return IngestResponse(
        doc_id=doc_id,
        filename=filename,
        total_pages=total_pages,
        facts_extracted=facts_extracted,
        adjudications_performed=adjudications_count,
        verdicts_summary=verdict_summary,
        latency_seconds=elapsed,
        llm_calls_made=llm_calls_made,
        extraction_mode=mode_str,
        execution_log=execution_log
    )

# ----------------- API ENDPOINTS -----------------

@app.post("/api/documents/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...), max_pages: int = Form(15)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    save_path = UPLOADS_DIR / file.filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return process_pdf_ingestion(save_path, file.filename, max_pages=max_pages)

@app.post("/api/starter/ingest")
def ingest_starter_dataset(dataset_name: str = Form("delhivery"), max_pages: int = Form(10)):
    """Ingest files from starter datasets directory."""
    target_dir = STARTER_DATA_DIR / dataset_name
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail=f"Starter dataset '{dataset_name}' not found.")

    pdf_files = sorted(list(target_dir.glob("*.pdf")))
    if not pdf_files:
        raise HTTPException(status_code=404, detail=f"No PDF files found in starter dataset '{dataset_name}'.")

    results = []
    for pdf_path in pdf_files:
        resp = process_pdf_ingestion(pdf_path, pdf_path.name, max_pages=max_pages)
        results.append(resp)

    return {
        "dataset": dataset_name,
        "processed_documents": len(results),
        "documents": results
    }

@app.get("/api/documents", response_model=List[DocumentMetadata])
def list_documents():
    return db.get_documents()

@app.get("/api/facts", response_model=List[Fact])
def list_facts(doc_id: Optional[str] = None, status: Optional[str] = None, q: Optional[str] = None):
    return db.get_facts(doc_id=doc_id, status=status, query=q)

@app.get("/api/facts/{fact_id}", response_model=FactDossier)
def get_fact_dossier(fact_id: str):
    fact = db.get_fact_by_id(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found.")
    
    verdicts = db.get_verdicts_for_fact(fact_id)
    
    # Collect witness facts
    witnesses = []
    for v in verdicts:
        other_id = v.fact_id_2 if v.fact_id_1 == fact_id else v.fact_id_1
        other_fact = db.get_fact_by_id(other_id)
        if other_fact:
            witnesses.append({
                "verdict_id": v.id,
                "verdict_type": v.verdict_type,
                "fact": other_fact,
                "final_reasoning": v.final_reasoning,
                "reconciliation_reason": v.reconciliation_reason,
                "similarity_score": v.similarity_score
            })

    doc = db.get_document_by_id(fact.doc_id)
    doc_name = doc.filename if doc else fact.evidence.doc_name

    return FactDossier(
        fact=fact,
        document_name=doc_name,
        verdicts=verdicts,
        witness_facts=witnesses
    )

class ReviewRequest(BaseModel):
    verdict_type: VerdictType
    notes: str

@app.post("/api/verdicts/{verdict_id}/review")
def review_verdict(verdict_id: str, req: ReviewRequest):
    db.update_verdict_review(verdict_id, req.verdict_type, req.notes)
    return {"status": "success", "verdict_id": verdict_id, "updated_verdict": req.verdict_type}

@app.post("/api/verdicts/{verdict_id}/tiebreak")
def chief_magistrate_tiebreak(verdict_id: str):
    verdicts = [v for v in db.get_all_verdicts() if v.id == verdict_id]
    if not verdicts:
        raise HTTPException(status_code=404, detail="Verdict not found.")
    v = verdicts[0]
    f1 = db.get_fact_by_id(v.fact_id_1)
    f2 = db.get_fact_by_id(v.fact_id_2)
    if not f1 or not f2:
        raise HTTPException(status_code=400, detail="Associated facts missing.")

    arb = courtroom.arbitrate_tiebreak(f1, f2, v.skeptic_reasoning, v.reconciler_reasoning)
    new_type = VerdictType(arb.get("verdict", VerdictType.RECONCILED.value))
    db.update_verdict_review(verdict_id, new_type, f"Chief Magistrate Arbiter resolution: {arb.get('final_reasoning')}")
    return {"status": "resolved", "verdict": new_type, "arbitration": arb}

@app.get("/api/showcases")
def get_showcases():
    return get_curated_showcase_exhibits()

@app.post("/api/showcases/reset")
def reset_showcases():
    db.clear_all()
    embedding_index.clear()
    seed_showcase_data(db, embedding_index)
    return {"status": "reset", "exhibits_count": len(get_curated_showcase_exhibits())}

class SettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    provider: Optional[str] = None
    similarity_threshold: Optional[float] = None

class TestKeyRequest(BaseModel):
    provider: str
    api_key: Optional[str] = ""

@app.get("/api/settings")
def get_settings():
    return {
        "llm_status": llm_client.get_status(),
        "similarity_threshold": embedding_index.similarity_threshold,
        "indexed_facts_count": len(embedding_index.index),
        "total_documents_count": len(db.get_documents()),
        "total_facts_count": len(db.get_facts())
    }

@app.post("/api/settings/test")
def test_settings_connection(req: TestKeyRequest):
    result = llm_client.validate_connection(req.provider, req.api_key or "")
    return result

@app.post("/api/settings")
def update_settings(settings: SettingsUpdate):
    if settings.provider is not None:
        llm_client.provider = settings.provider
    if settings.api_key is not None:
        llm_client.api_key = settings.api_key.strip()
    if settings.similarity_threshold is not None:
        embedding_index.similarity_threshold = settings.similarity_threshold

    # Re-sync agents with client
    detective.llm = llm_client
    courtroom.llm = llm_client

    return {
        "status": "updated",
        "settings": get_settings()
    }

# ----------------- STATIC FRONTEND -----------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

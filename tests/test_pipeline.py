import pytest
import numpy as np
from pathlib import Path

from backend.app.models import Fact, Evidence, Verdict, VerdictType, FactStatus, JudgeOpinion, DocumentMetadata
from backend.app.pdf_parser import PDFParser, normalize_text
from backend.app.embeddings import EmbeddingIndex, build_fact_text, compute_local_embedding
from backend.app.detective import DetectiveAgent
from backend.app.courtroom import CourtroomAgent
from backend.app.database import Database
from backend.app.showcase import get_curated_showcase_exhibits, seed_showcase_data

def test_text_normalization():
    raw = "Delhivery   Limited—incorporated in 2011.\n\xa0Revenue: ₹81,411.39 million."
    norm = normalize_text(raw)
    assert "Delhivery Limited-incorporated in 2011." in norm
    assert "Revenue: ₹81,411.39 million." in norm
    assert "\xa0" not in norm

def test_embedding_vector_generation():
    text1 = build_fact_text("India Real GDP", "expanded by", "8.2%", {"fiscal_year": "FY24"})
    text2 = build_fact_text("India GDP Growth", "accelerated to", "8.2 per cent", {"fiscal_year": "FY24"})
    text3 = build_fact_text("Apple Inc", "sold units", "50 million", {"quarter": "Q1"})

    vec1 = compute_local_embedding(text1)
    vec2 = compute_local_embedding(text2)
    vec3 = compute_local_embedding(text3)

    assert len(vec1) == 256
    assert abs(np.linalg.norm(vec1) - 1.0) < 1e-4

    # Similarity between related facts should be significantly higher than unrelated
    sim_1_2 = float(np.dot(vec1, vec2))
    sim_1_3 = float(np.dot(vec1, vec3))

    assert sim_1_2 > sim_1_3
    assert sim_1_2 > 0.45

def test_embedding_index_candidate_search():
    index = EmbeddingIndex(similarity_threshold=0.45)
    index.add_fact("f1", "Delhivery | revenue | ₹81,411 million (FY24)", {"doc_id": "doc_1"})
    index.add_fact("f2", "Delhivery | revenue | ₹36,465 million (FY21)", {"doc_id": "doc_2"})
    index.add_fact("f3", "India GDP | growth | 8.2%", {"doc_id": "doc_3"})

    candidates = index.search_candidates("Delhivery revenue in 2024", top_k=2)
    assert len(candidates) >= 1
    assert candidates[0]["fact_id"] in ["f1", "f2"]

def test_courtroom_opinion_combination():
    courtroom = CourtroomAgent()
    
    fact1 = Fact(
        id="f1",
        doc_id="doc1",
        subject="India GDP",
        predicate="expanded by",
        object="8.2%",
        qualifiers={"fiscal_year": "FY24"},
        credibility=0.98,
        evidence=Evidence(doc_id="doc1", doc_name="Doc1.pdf", page_number=1, exact_text_span="GDP grew 8.2%")
    )
    fact2 = Fact(
        id="f2",
        doc_id="doc2",
        subject="India GDP",
        predicate="grew at",
        object="8.2 per cent",
        qualifiers={"fiscal_year": "FY24"},
        credibility=0.99,
        evidence=Evidence(doc_id="doc2", doc_name="Doc2.pdf", page_number=5, exact_text_span="GDP accelerated to 8.2 per cent")
    )

    # 1. Test Corroboration synthesis
    skeptic_corrob = JudgeOpinion(
        judge_name="Skeptic",
        stance="CORROBORATION",
        reasoning="Identical metric across documents.",
        suggested_verdict=VerdictType.CORROBORATED
    )
    reconciler_corrob = JudgeOpinion(
        judge_name="Reconciler",
        stance="CORROBORATION",
        reasoning="Both report 8.2% for FY24.",
        suggested_verdict=VerdictType.CORROBORATED
    )

    verdict_type, reason, recon_reason, is_sup, sup_id = courtroom._combine_opinions(
        fact1, fact2, skeptic_corrob, reconciler_corrob
    )
    assert verdict_type == VerdictType.CORROBORATED
    assert not is_sup

    # 2. Test Reconciliation synthesis
    skeptic_conflict = JudgeOpinion(
        judge_name="Skeptic",
        stance="CONTRADICTION",
        reasoning="Numeric difference: 36,465M vs 81,411M.",
        suggested_verdict=VerdictType.CONTRADICTED
    )
    reconciler_recon = JudgeOpinion(
        judge_name="Reconciler",
        stance="RECONCILIATION",
        reasoning="FY21 vs FY24 time periods account for growth.",
        suggested_verdict=VerdictType.RECONCILED,
        reconciliation_reason="Different fiscal years (FY21 vs FY24)."
    )

    verdict_type2, reason2, recon_reason2, is_sup2, _ = courtroom._combine_opinions(
        fact1, fact2, skeptic_conflict, reconciler_recon
    )
    assert verdict_type2 == VerdictType.RECONCILED
    assert recon_reason2 == "Different fiscal years (FY21 vs FY24)."

    # 3. Test Supersession synthesis
    reconciler_sup = JudgeOpinion(
        judge_name="Reconciler",
        stance="SUPERSEDED",
        reasoning="FY24 filing updates director status.",
        suggested_verdict=VerdictType.SUPERSEDED_BY,
        is_superseded=True
    )
    verdict_type3, reason3, _, is_sup3, sup_id3 = courtroom._combine_opinions(
        fact1, fact2, skeptic_conflict, reconciler_sup
    )
    assert verdict_type3 == VerdictType.SUPERSEDED_BY
    assert is_sup3 is True
    assert sup_id3 == fact1.id

def test_database_crud_operations(tmp_path):
    test_db_path = tmp_path / "test.db"
    db = Database(db_path=test_db_path)
    
    doc = DocumentMetadata(
        id="test_doc_1",
        filename="sample.pdf",
        filepath="starter_data/sample.pdf",
        total_pages=5
    )
    db.add_document(doc)
    docs = db.get_documents()
    assert any(d.id == "test_doc_1" for d in docs)

    fact = Fact(
        id="test_fact_1",
        doc_id="test_doc_1",
        subject="Delhivery",
        predicate="founded in",
        object="2011",
        qualifiers={"country": "India"},
        credibility=0.99,
        evidence=Evidence(doc_id="test_doc_1", doc_name="sample.pdf", page_number=2, exact_text_span="Delhivery was founded in 2011")
    )
    db.add_fact(fact)
    retrieved = db.get_fact_by_id("test_fact_1")
    assert retrieved is not None
    assert retrieved.subject == "Delhivery"
    assert retrieved.credibility == 0.99
    assert retrieved.evidence.page_number == 2

    # Update status to SUPERSEDED
    db.update_fact_status("test_fact_1", FactStatus.SUPERSEDED)
    updated = db.get_fact_by_id("test_fact_1")
    assert updated.status == FactStatus.SUPERSEDED

def test_showcase_exhibits_integrity():
    exhibits = get_curated_showcase_exhibits()
    assert len(exhibits) == 5

    case_types = [e["verdict_type"] for e in exhibits]
    assert VerdictType.CORROBORATED.value in case_types
    assert VerdictType.CONTRADICTED.value in case_types
    assert VerdictType.RECONCILED.value in case_types
    assert VerdictType.SUPERSEDED_BY.value in case_types
    assert VerdictType.HUNG_JURY.value in case_types

    # Verify both datasets are represented
    datasets = set(e["dataset"] for e in exhibits)
    assert "India Macroeconomy" in datasets
    assert "Delhivery Corporate Filings" in datasets

    # Verify evidence traceability
    for e in exhibits:
        assert "exact_text_span" in e["fact_1"]["evidence"]
        assert "page_number" in e["fact_1"]["evidence"]
        assert len(e["fact_1"]["evidence"]["exact_text_span"]) > 10
        assert "exact_text_span" in e["fact_2"]["evidence"]
        assert "page_number" in e["fact_2"]["evidence"]
        assert len(e["fact_2"]["evidence"]["exact_text_span"]) > 10
        assert "skeptic_reasoning" in e["courtroom"]
        assert "reconciler_reasoning" in e["courtroom"]

def test_fact_supersession_audit_chain(tmp_path):
    test_db_path = tmp_path / "test_supersession.db"
    db = Database(db_path=test_db_path)

    doc = DocumentMetadata(id="doc_corp", filename="filing.pdf", filepath="filing.pdf", total_pages=10)
    db.add_document(doc)

    fact_old = Fact(
        id="fact_old_1",
        doc_id="doc_corp",
        subject="Kapil Bharti",
        predicate="served as",
        object="Executive Director",
        credibility=0.95,
        status=FactStatus.ACTIVE,
        extraction_method="frontier_llm",
        evidence=Evidence(doc_id="doc_corp", doc_name="filing.pdf", page_number=1, exact_text_span="Kapil Bharti is Executive Director")
    )
    db.add_fact(fact_old)

    fact_new = Fact(
        id="fact_new_2",
        doc_id="doc_corp",
        subject="Kapil Bharti",
        predicate="transitioned to",
        object="Non-Executive Director",
        credibility=0.96,
        status=FactStatus.ACTIVE,
        extraction_method="frontier_llm",
        supersedes_fact_id="fact_old_1",
        evidence=Evidence(doc_id="doc_corp", doc_name="filing.pdf", page_number=2, exact_text_span="Kapil Bharti transitioned to Non-Executive Director")
    )
    db.add_fact(fact_new)

    # Retire old fact
    db.update_fact_status("fact_old_1", FactStatus.SUPERSEDED, superseded_by="fact_new_2", superseded_at="2024-05-30T10:00:00Z")

    retrieved_old = db.get_fact_by_id("fact_old_1")
    retrieved_new = db.get_fact_by_id("fact_new_2")

    assert retrieved_old.status == FactStatus.SUPERSEDED
    assert retrieved_old.superseded_by == "fact_new_2"
    assert retrieved_old.superseded_at == "2024-05-30T10:00:00Z"
    assert retrieved_new.supersedes_fact_id == "fact_old_1"
    assert retrieved_new.extraction_method == "frontier_llm"

def test_empty_key_handshake_validation():
    from backend.app.llm_client import LLMClient
    client = LLMClient()
    res = client.validate_connection("gemini", "")
    assert res["ok"] is False
    assert "no api key provided" in res["error"].lower()


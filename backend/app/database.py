import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DB_PATH
from .models import Fact, Evidence, Verdict, DocumentMetadata, FactStatus, VerdictType

import hashlib

def get_doc_id(filename: str) -> str:
    """Deterministic document ID from filename."""
    clean = Path(filename).name.strip().lower()
    return f"doc_{hashlib.md5(clean.encode()).hexdigest()[:10]}"

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target = db_path or DB_PATH
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        total_pages INTEGER NOT NULL,
        uploaded_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facts (
        id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object TEXT NOT NULL,
        qualifiers_json TEXT NOT NULL,
        credibility REAL NOT NULL,
        status TEXT NOT NULL,
        extraction_method TEXT NOT NULL DEFAULT 'frontier_llm',
        superseded_by TEXT,
        superseded_at TEXT,
        supersedes_fact_id TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(doc_id) REFERENCES documents(id)
    );
    """)

    # Check if extra columns exist, add if missing for backward-compatible migration
    cursor.execute("PRAGMA table_info(facts)")
    columns = [col[1] for col in cursor.fetchall()]
    if "extraction_method" not in columns:
        cursor.execute("ALTER TABLE facts ADD COLUMN extraction_method TEXT NOT NULL DEFAULT 'frontier_llm'")
    if "superseded_by" not in columns:
        cursor.execute("ALTER TABLE facts ADD COLUMN superseded_by TEXT")
    if "superseded_at" not in columns:
        cursor.execute("ALTER TABLE facts ADD COLUMN superseded_at TEXT")
    if "supersedes_fact_id" not in columns:
        cursor.execute("ALTER TABLE facts ADD COLUMN supersedes_fact_id TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id TEXT PRIMARY KEY,
        fact_id TEXT NOT NULL,
        doc_id TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        exact_text_span TEXT NOT NULL,
        char_start INTEGER,
        char_end INTEGER,
        FOREIGN KEY(fact_id) REFERENCES facts(id),
        FOREIGN KEY(doc_id) REFERENCES documents(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verdicts (
        id TEXT PRIMARY KEY,
        fact_id_1 TEXT NOT NULL,
        fact_id_2 TEXT NOT NULL,
        verdict_type TEXT NOT NULL,
        skeptic_reasoning TEXT NOT NULL,
        reconciler_reasoning TEXT NOT NULL,
        final_reasoning TEXT NOT NULL,
        reconciliation_reason TEXT,
        is_superseded INTEGER NOT NULL DEFAULT 0,
        superseded_fact_id TEXT,
        similarity_score REAL NOT NULL DEFAULT 0.0,
        created_at TEXT NOT NULL,
        human_reviewed INTEGER NOT NULL DEFAULT 0,
        human_notes TEXT,
        FOREIGN KEY(fact_id_1) REFERENCES facts(id),
        FOREIGN KEY(fact_id_2) REFERENCES facts(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        fact_id TEXT PRIMARY KEY,
        vector_json TEXT NOT NULL,
        FOREIGN KEY(fact_id) REFERENCES facts(id)
    );
    """)

    conn.commit()
    conn.close()

class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        init_db(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def clear_all(self):
        """Purge all records across all tables."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM verdicts")
        cursor.execute("DELETE FROM evidence")
        cursor.execute("DELETE FROM facts")
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM embeddings")
        conn.commit()
        conn.close()

    def add_document(self, doc: DocumentMetadata):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO documents (id, filename, filepath, total_pages, uploaded_at) VALUES (?, ?, ?, ?, ?)",
            (doc.id, doc.filename, doc.filepath, doc.total_pages, doc.uploaded_at)
        )
        conn.commit()
        conn.close()

    def get_documents(self) -> List[DocumentMetadata]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, COUNT(f.id) as fact_count 
            FROM documents d 
            LEFT JOIN facts f ON d.id = f.doc_id 
            GROUP BY d.id 
            ORDER BY d.uploaded_at DESC
        """)
        rows = cursor.fetchall()
        docs = []
        for r in rows:
            docs.append(DocumentMetadata(
                id=r["id"],
                filename=r["filename"],
                filepath=r["filepath"],
                total_pages=r["total_pages"],
                uploaded_at=r["uploaded_at"],
                fact_count=r["fact_count"]
            ))
        conn.close()
        return docs

    def get_document_by_id(self, doc_id: str) -> Optional[DocumentMetadata]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        r = cursor.fetchone()
        conn.close()
        if not r:
            return None
        return DocumentMetadata(
            id=r["id"],
            filename=r["filename"],
            filepath=r["filepath"],
            total_pages=r["total_pages"],
            uploaded_at=r["uploaded_at"]
        )

    def add_fact(self, fact: Fact):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO facts 
               (id, doc_id, subject, predicate, object, qualifiers_json, credibility, status,
                extraction_method, superseded_by, superseded_at, supersedes_fact_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fact.id, fact.doc_id, fact.subject, fact.predicate, fact.object,
             json.dumps(fact.qualifiers), fact.credibility, fact.status.value,
             fact.extraction_method, fact.superseded_by, fact.superseded_at, fact.supersedes_fact_id, fact.created_at)
        )
        # Add evidence
        ev_id = f"ev_{fact.id}"
        cursor.execute(
            """INSERT OR REPLACE INTO evidence 
               (id, fact_id, doc_id, page_number, exact_text_span, char_start, char_end)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ev_id, fact.id, fact.evidence.doc_id, fact.evidence.page_number,
             fact.evidence.exact_text_span, fact.evidence.char_start, fact.evidence.char_end)
        )
        conn.commit()
        conn.close()

    def update_fact_status(self, fact_id: str, new_status: FactStatus, superseded_by: Optional[str] = None, superseded_at: Optional[str] = None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if superseded_by:
            cursor.execute(
                "UPDATE facts SET status = ?, superseded_by = ?, superseded_at = ? WHERE id = ?",
                (new_status.value, superseded_by, superseded_at, fact_id)
            )
        else:
            cursor.execute("UPDATE facts SET status = ? WHERE id = ?", (new_status.value, fact_id))
        conn.commit()
        conn.close()

    def get_fact_by_id(self, fact_id: str) -> Optional[Fact]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, e.page_number, e.exact_text_span, e.char_start, e.char_end, d.filename as doc_name
            FROM facts f
            JOIN evidence e ON f.id = e.fact_id
            JOIN documents d ON f.doc_id = d.id
            WHERE f.id = ?
        """, (fact_id,))
        r = cursor.fetchone()
        conn.close()
        if not r:
            return None
        return self._row_to_fact(r)

    def get_facts(self, doc_id: Optional[str] = None, status: Optional[str] = None, query: Optional[str] = None) -> List[Fact]:
        conn = self._get_conn()
        cursor = conn.cursor()
        sql = """
            SELECT f.*, e.page_number, e.exact_text_span, e.char_start, e.char_end, d.filename as doc_name
            FROM facts f
            JOIN evidence e ON f.id = e.fact_id
            JOIN documents d ON f.doc_id = d.id
            WHERE 1=1
        """
        params = []
        if doc_id:
            sql += " AND f.doc_id = ?"
            params.append(doc_id)
        if status:
            sql += " AND f.status = ?"
            params.append(status)
        if query:
            sql += " AND (f.subject LIKE ? OR f.predicate LIKE ? OR f.object LIKE ? OR e.exact_text_span LIKE ?)"
            q_param = f"%{query}%"
            params.extend([q_param, q_param, q_param, q_param])

        sql += " ORDER BY f.created_at DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        facts = [self._row_to_fact(r) for r in rows]
        conn.close()
        return facts

    def _row_to_fact(self, r: sqlite3.Row) -> Fact:
        qualifiers = {}
        try:
            qualifiers = json.loads(r["qualifiers_json"])
        except Exception:
            pass
        
        evidence = Evidence(
            doc_id=r["doc_id"],
            doc_name=r["doc_name"],
            page_number=r["page_number"],
            exact_text_span=r["exact_text_span"],
            char_start=r["char_start"],
            char_end=r["char_end"]
        )

        keys = r.keys()
        extraction_method = r["extraction_method"] if "extraction_method" in keys and r["extraction_method"] else "frontier_llm"
        superseded_by = r["superseded_by"] if "superseded_by" in keys else None
        superseded_at = r["superseded_at"] if "superseded_at" in keys else None
        supersedes_fact_id = r["supersedes_fact_id"] if "supersedes_fact_id" in keys else None

        return Fact(
            id=r["id"],
            doc_id=r["doc_id"],
            subject=r["subject"],
            predicate=r["predicate"],
            object=r["object"],
            qualifiers=qualifiers,
            credibility=float(r["credibility"]),
            status=FactStatus(r["status"]),
            extraction_method=extraction_method,
            superseded_by=superseded_by,
            superseded_at=superseded_at,
            supersedes_fact_id=supersedes_fact_id,
            evidence=evidence,
            created_at=r["created_at"]
        )

    def add_verdict(self, verdict: Verdict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO verdicts
               (id, fact_id_1, fact_id_2, verdict_type, skeptic_reasoning, reconciler_reasoning,
                final_reasoning, reconciliation_reason, is_superseded, superseded_fact_id,
                similarity_score, created_at, human_reviewed, human_notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (verdict.id, verdict.fact_id_1, verdict.fact_id_2, verdict.verdict_type.value,
             verdict.skeptic_reasoning, verdict.reconciler_reasoning, verdict.final_reasoning,
             verdict.reconciliation_reason, 1 if verdict.is_superseded else 0,
             verdict.superseded_fact_id, verdict.similarity_score, verdict.created_at,
             1 if verdict.human_reviewed else 0, verdict.human_notes)
        )
        conn.commit()
        conn.close()

    def get_verdicts_for_fact(self, fact_id: str) -> List[Verdict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM verdicts 
            WHERE fact_id_1 = ? OR fact_id_2 = ?
            ORDER BY created_at DESC
        """, (fact_id, fact_id))
        rows = cursor.fetchall()
        verdicts = [self._row_to_verdict(r) for r in rows]
        conn.close()
        return verdicts

    def get_all_verdicts(self) -> List[Verdict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verdicts ORDER BY created_at DESC")
        rows = cursor.fetchall()
        verdicts = [self._row_to_verdict(r) for r in rows]
        conn.close()
        return verdicts

    def update_verdict_review(self, verdict_id: str, new_verdict_type: VerdictType, notes: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE verdicts 
            SET verdict_type = ?, human_reviewed = 1, human_notes = ? 
            WHERE id = ?
        """, (new_verdict_type.value, notes, verdict_id))
        conn.commit()
        conn.close()

    def _row_to_verdict(self, r: sqlite3.Row) -> Verdict:
        return Verdict(
            id=r["id"],
            fact_id_1=r["fact_id_1"],
            fact_id_2=r["fact_id_2"],
            verdict_type=VerdictType(r["verdict_type"]),
            skeptic_reasoning=r["skeptic_reasoning"],
            reconciler_reasoning=r["reconciler_reasoning"],
            final_reasoning=r["final_reasoning"],
            reconciliation_reason=r["reconciliation_reason"],
            is_superseded=bool(r["is_superseded"]),
            superseded_fact_id=r["superseded_fact_id"],
            similarity_score=float(r["similarity_score"]),
            created_at=r["created_at"],
            human_reviewed=bool(r["human_reviewed"]),
            human_notes=r["human_notes"]
        )

    def save_embedding(self, fact_id: str, vector: List[float]):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO embeddings (fact_id, vector_json) VALUES (?, ?)", (fact_id, json.dumps(vector)))
        conn.commit()
        conn.close()

    def load_all_embeddings(self) -> Dict[str, List[float]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT fact_id, vector_json FROM embeddings")
        rows = cursor.fetchall()
        result = {}
        for r in rows:
            try:
                result[r["fact_id"]] = json.loads(r["vector_json"])
            except Exception:
                pass
        conn.close()
        return result

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import uuid
import datetime

class VerdictType(str, Enum):
    CORROBORATED = "CORROBORATED"
    CONTRADICTED = "CONTRADICTED"
    RECONCILED = "RECONCILED"
    HUNG_JURY = "HUNG_JURY"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    NO_RELEVANT_MATCH = "NO_RELEVANT_MATCH"

class FactStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"

class Evidence(BaseModel):
    doc_id: str
    doc_name: str
    page_number: int
    exact_text_span: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None

class FactBase(BaseModel):
    subject: str
    predicate: str
    object: str
    qualifiers: Dict[str, Any] = Field(default_factory=dict)
    credibility: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence: Evidence

class Fact(FactBase):
    id: str = Field(default_factory=lambda: f"fact_{uuid.uuid4().hex[:10]}")
    doc_id: str
    status: FactStatus = FactStatus.ACTIVE
    extraction_method: str = "frontier_llm"  # "frontier_llm" or "heuristic_fallback"
    superseded_by: Optional[str] = None
    superseded_at: Optional[str] = None
    supersedes_fact_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def statement(self) -> str:
        qual_str = ""
        if self.qualifiers:
            qual_str = f" [{', '.join(f'{k}: {v}' for k, v in self.qualifiers.items())}]"
        return f"{self.subject} -> {self.predicate} -> {self.object}{qual_str}"

class JudgeOpinion(BaseModel):
    judge_name: str  # "Skeptic" or "Reconciler"
    stance: str  # "CONTRADICTION", "CORROBORATION", "RECONCILIATION", "SUPERSEDED", "HUNG"
    reasoning: str
    suggested_verdict: VerdictType
    reconciliation_reason: Optional[str] = None
    is_superseded: bool = False
    supersedes_target_id: Optional[str] = None

class Verdict(BaseModel):
    id: str = Field(default_factory=lambda: f"vrd_{uuid.uuid4().hex[:10]}")
    fact_id_1: str
    fact_id_2: str
    verdict_type: VerdictType
    skeptic_reasoning: str
    reconciler_reasoning: str
    final_reasoning: str
    reconciliation_reason: Optional[str] = None
    is_superseded: bool = False
    superseded_fact_id: Optional[str] = None
    similarity_score: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    human_reviewed: bool = False
    human_notes: Optional[str] = None

class DocumentMetadata(BaseModel):
    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    filename: str
    filepath: str
    total_pages: int
    uploaded_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    fact_count: int = 0

class FactDossier(BaseModel):
    fact: Fact
    document_name: str
    verdicts: List[Verdict] = Field(default_factory=list)
    witness_facts: List[Dict[str, Any]] = Field(default_factory=list)

class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    facts_extracted: int
    adjudications_performed: int
    verdicts_summary: Dict[str, int]
    latency_seconds: Optional[float] = None
    llm_calls_made: Optional[int] = 0
    extraction_mode: Optional[str] = "heuristic_fallback"
    execution_log: Optional[List[str]] = Field(default_factory=list)

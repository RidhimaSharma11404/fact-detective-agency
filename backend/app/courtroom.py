import json
from typing import Dict, Any, Optional, Tuple, List
from .models import Fact, Verdict, VerdictType, JudgeOpinion, FactStatus
from .llm_client import LLMClient, extract_json

SKEPTIC_SYSTEM_PROMPT = """You are "The Skeptic", an adversarial judge in the Courtroom of The Fact Detective Agency.
Your bias and role: You aggressively search for contradictions, discrepancies, incompatible assertions, and metric mismatches between two factual claims.

You must evaluate whether Fact A and Fact B make conflicting or incompatible statements.
If there are different numbers, different dates, different statuses, or contrasting assertions, point them out forcefully.
If the facts are clearly stating the exact same thing (even if phrased differently), you may concede corroboration.

Return JSON in this format:
{
  "stance": "CONTRADICTION" | "CORROBORATION" | "RECONCILIATION" | "SUPERSEDED" | "HUNG",
  "suggested_verdict": "CONTRADICTED" | "CORROBORATED" | "RECONCILED" | "SUPERSEDED_BY" | "HUNG_JURY",
  "reasoning": "Detailed breakdown of the tension, conflict, or alignment between the facts.",
  "is_superseded": false,
  "supersedes_target": null
}
"""

RECONCILER_SYSTEM_PROMPT = """You are "The Reconciler", an investigative contextual judge in the Courtroom of The Fact Detective Agency.
Your bias and role: You investigate whether apparent contradictions between Fact A and Fact B can be logically reconciled by looking at context:
- Time differences (e.g., FY22 vs FY24, Q3 vs Q4, 2021 vs 2024)
- Scope differences (e.g., Consolidated vs Standalone, Domestic vs International, Core vs Total)
- Unit differences (e.g., Lakhs vs Crores vs Millions, % of GDP vs nominal INR)
- Revision / Supersession (e.g., a newer audited report updating previous provisional figures or director status changes)

If a genuine conflict exists with no contextual explanation, you must concede contradiction.
If the facts state the same truth, acknowledge corroboration.

Return JSON in this format:
{
  "stance": "RECONCILIATION" | "CORROBORATION" | "CONTRADICTION" | "SUPERSEDED" | "HUNG",
  "suggested_verdict": "RECONCILED" | "CORROBORATED" | "CONTRADICTED" | "SUPERSEDED_BY" | "HUNG_JURY",
  "reconciliation_reason": "Specific explanation of how time/scope/units/vintage resolve the tension (or null if none)",
  "reasoning": "Detailed contextual analysis.",
  "is_superseded": false,
  "supersedes_target": null
}
"""

CHIEF_MAGISTRATE_SYSTEM_PROMPT = """You are "The Chief Magistrate", the senior tiebreaker judge of The Fact Detective Agency Courtroom.
Two judges—The Skeptic (biased toward contradictions) and The Reconciler (biased toward contextual explanations)—have reached a deadlocked HUNG JURY.

Review Fact A, Fact B, the Skeptic's argument, and the Reconciler's argument.
Determine whether the Reconciler's contextual explanation is logically sound and valid, or if the Skeptic's contradiction remains unresolvable.
Or determine if this is an irreconcilable ambiguity that must remain flagged for human review.

Return JSON:
{
  "verdict": "RECONCILED" | "CONTRADICTED" | "CORROBORATED" | "SUPERSEDED_BY" | "HUNG_JURY",
  "final_reasoning": "Authoritative resolution evaluating both judges' arguments.",
  "reconciliation_reason": "Clear contextual reconciliation statement if reconciled, otherwise null.",
  "is_superseded": false
}
"""

class CourtroomAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def adjudicate_pair(self, fact_1: Fact, fact_2: Fact, similarity_score: float = 0.0) -> Verdict:
        """
        Run the dual-judge adjudication process over two candidate facts.
        """
        pair_prompt = f"""Fact A:
- Subject: {fact_1.subject}
- Predicate: {fact_1.predicate}
- Object: {fact_1.object}
- Qualifiers: {json.dumps(fact_1.qualifiers)}
- Source Doc: {fact_1.evidence.doc_name} (Page {fact_1.evidence.page_number})
- Exact Evidence: "{fact_1.evidence.exact_text_span}"
- Credibility: {fact_1.credibility}

Fact B:
- Subject: {fact_2.subject}
- Predicate: {fact_2.predicate}
- Object: {fact_2.object}
- Qualifiers: {json.dumps(fact_2.qualifiers)}
- Source Doc: {fact_2.evidence.doc_name} (Page {fact_2.evidence.page_number})
- Exact Evidence: "{fact_2.evidence.exact_text_span}"
- Credibility: {fact_2.credibility}
"""

        # 1. Run Skeptic Judge
        skeptic_raw = self.llm.generate(SKEPTIC_SYSTEM_PROMPT, pair_prompt, temperature=0.15)
        skeptic_json = extract_json(skeptic_raw) or {}
        skeptic_opinion = JudgeOpinion(
            judge_name="Skeptic",
            stance=skeptic_json.get("stance", "CONTRADICTION"),
            reasoning=skeptic_json.get("reasoning", "The Skeptic noted potential divergence in claims across documents."),
            suggested_verdict=skeptic_json.get("suggested_verdict", VerdictType.CONTRADICTED),
            is_superseded=skeptic_json.get("is_superseded", False)
        )

        # 2. Run Reconciler Judge
        reconciler_raw = self.llm.generate(RECONCILER_SYSTEM_PROMPT, pair_prompt, temperature=0.15)
        reconciler_json = extract_json(reconciler_raw) or {}
        reconciler_opinion = JudgeOpinion(
            judge_name="Reconciler",
            stance=reconciler_json.get("stance", "RECONCILIATION"),
            reasoning=reconciler_json.get("reasoning", "The Reconciler analyzed temporal, scope, and unit context."),
            suggested_verdict=reconciler_json.get("suggested_verdict", VerdictType.RECONCILED),
            reconciliation_reason=reconciler_json.get("reconciliation_reason"),
            is_superseded=reconciler_json.get("is_superseded", False)
        )

        # 3. Verdict Combination & Lifecycle Arbitration
        verdict_type, final_reasoning, recon_reason, is_superseded, superseded_id = self._combine_opinions(
            fact_1, fact_2, skeptic_opinion, reconciler_opinion
        )

        return Verdict(
            fact_id_1=fact_1.id,
            fact_id_2=fact_2.id,
            verdict_type=verdict_type,
            skeptic_reasoning=skeptic_opinion.reasoning,
            reconciler_reasoning=reconciler_opinion.reasoning,
            final_reasoning=final_reasoning,
            reconciliation_reason=recon_reason,
            is_superseded=is_superseded,
            superseded_fact_id=superseded_id,
            similarity_score=similarity_score
        )

    def arbitrate_tiebreak(self, fact_1: Fact, fact_2: Fact, skeptic_reasoning: str, reconciler_reasoning: str) -> Dict[str, Any]:
        """Chief Magistrate tiebreak pass for HUNG_JURY verdicts."""
        prompt = f"""Fact A: {fact_1.statement} (Doc: {fact_1.evidence.doc_name}, Page: {fact_1.evidence.page_number})
Evidence A: "{fact_1.evidence.exact_text_span}"

Fact B: {fact_2.statement} (Doc: {fact_2.evidence.doc_name}, Page: {fact_2.evidence.page_number})
Evidence B: "{fact_2.evidence.exact_text_span}"

Skeptic's Argument:
{skeptic_reasoning}

Reconciler's Argument:
{reconciler_reasoning}
"""
        raw = self.llm.generate(CHIEF_MAGISTRATE_SYSTEM_PROMPT, prompt, temperature=0.1)
        parsed = extract_json(raw) or {}
        return {
            "verdict": parsed.get("verdict", "RECONCILED"),
            "final_reasoning": parsed.get("final_reasoning", "The Chief Magistrate resolved the deadlock upon contextual review."),
            "reconciliation_reason": parsed.get("reconciliation_reason"),
            "is_superseded": parsed.get("is_superseded", False)
        }

    def _combine_opinions(
        self,
        fact_1: Fact,
        fact_2: Fact,
        skeptic: JudgeOpinion,
        reconciler: JudgeOpinion
    ) -> Tuple[VerdictType, str, Optional[str], bool, Optional[str]]:
        """Synthesize judge opinions and lifecycle rules into an authoritative verdict."""
        # 1. Supersession Check (Newer document updates older fact)
        if skeptic.is_superseded or reconciler.is_superseded or skeptic.suggested_verdict == VerdictType.SUPERSEDED_BY or reconciler.suggested_verdict == VerdictType.SUPERSEDED_BY:
            # Fact 2 (newly ingested) supersedes Fact 1 (older)
            reason = f"Fact from '{fact_2.evidence.doc_name}' updates and supersedes historical claim in '{fact_1.evidence.doc_name}'."
            return VerdictType.SUPERSEDED_BY, reason, None, True, fact_1.id

        # 2. Both agree on Corroboration
        if skeptic.suggested_verdict == VerdictType.CORROBORATED and reconciler.suggested_verdict == VerdictType.CORROBORATED:
            reason = "Both judges agree that both documents independently substantiate the same underlying factual assertion."
            return VerdictType.CORROBORATED, reason, None, False, None

        # 3. Both agree on Contradiction
        if skeptic.suggested_verdict == VerdictType.CONTRADICTED and reconciler.suggested_verdict == VerdictType.CONTRADICTED:
            reason = "Both judges agree that the documents make conflicting, irreconcilable claims under equivalent conditions."
            return VerdictType.CONTRADICTED, reason, None, False, None

        # 4. Reconciler found a substantiated contextual explanation
        if reconciler.suggested_verdict == VerdictType.RECONCILED and reconciler.reconciliation_reason:
            recon_reason = reconciler.reconciliation_reason
            reason = f"Apparent tension resolved by contextual difference: {recon_reason}"
            return VerdictType.RECONCILED, reason, recon_reason, False, None

        # 5. One corroborates and the other reconciles
        if (skeptic.suggested_verdict == VerdictType.CORROBORATED and reconciler.suggested_verdict == VerdictType.RECONCILED) or \
           (skeptic.suggested_verdict == VerdictType.RECONCILED and reconciler.suggested_verdict == VerdictType.CORROBORATED):
            recon_reason = reconciler.reconciliation_reason or "Phrased under compatible reporting perspectives."
            return VerdictType.CORROBORATED, "Judges agreed on substantive factual alignment.", recon_reason, False, None

        # 6. Deadlock / Disagreement -> HUNG_JURY
        reason = "Judges disagreed on whether contextual factors account for the discrepancy. Flagged for human review / Chief Magistrate arbitration."
        return VerdictType.HUNG_JURY, reason, reconciler.reconciliation_reason, False, None

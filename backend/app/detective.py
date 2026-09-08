import re
import json
import hashlib
from typing import List, Dict, Any, Optional
from .models import Fact, Evidence, FactStatus
from .llm_client import LLMClient, extract_json
from .pdf_parser import PDFParser, normalize_text

DETECTIVE_SYSTEM_PROMPT = """You are "The Detective", an expert fact extraction agent.
Your objective is to extract atomic, self-contained factual claims from the provided document page.

Rules:
1. Extract atomic facts: Each fact must have a clear (subject, predicate, object) structure.
2. Infer qualifiers dynamically from context (time period, fiscal year, scope, units, currency, reporting standard, etc.). Do NOT use a hardcoded schema.
3. Trace exact evidence: You must quote the EXACT text span from the document where the fact is stated.
4. Score credibility from 0.0 to 1.0 based on universal linguistic certainty markers:
   - 0.90 to 1.0: Audited historical data, tables, definitive factual past/present statements.
   - 0.70 to 0.89: Descriptive management commentary, unambiguous narrative statements.
   - 0.50 to 0.69: Hedged or estimated language ("estimated at", "approximately", "around").
   - 0.20 to 0.49: Forward-looking statements, management expectations, guidance, targets ("expects", "aims to", "projected").
5. Do not hallucinate. If no clear atomic facts exist on the page, return an empty list.

Return JSON in this EXACT format:
{
  "facts": [
    {
      "subject": "Delhivery",
      "predicate": "reported consolidated revenue from contracts with customers",
      "object": "81,411.39 million INR",
      "qualifiers": {
        "fiscal_year": "FY24",
        "period_end": "March 31, 2024",
        "basis": "consolidated",
        "unit": "million INR"
      },
      "exact_text_span": "Revenue from contracts with customers for the year ended March 31, 2024 was ₹81,411.39 million",
      "credibility": 0.98,
      "credibility_reasoning": "Audited consolidated financial statement figure stated as historical fact."
    }
  ]
}
"""

class DetectiveAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def extract_facts_from_page(self, doc_id: str, doc_name: str, page_num: int, page_text: str) -> List[Fact]:
        """Extract atomic facts with evidence and credibility from a single page."""
        normalized = normalize_text(page_text)
        if len(normalized) < 40:
            return []

        user_prompt = f"""Document: {doc_name}
Page Number: {page_num}

Page Text:
\"\"\"{page_text[:4000]}\"\"\"

Extract all distinct atomic facts following the required JSON schema."""

        response_text = self.llm.generate(DETECTIVE_SYSTEM_PROMPT, user_prompt, temperature=0.1)
        parsed = extract_json(response_text)
        
        extracted_facts: List[Fact] = []

        if parsed and isinstance(parsed, dict) and "facts" in parsed and isinstance(parsed["facts"], list):
            for item in parsed["facts"]:
                if not isinstance(item, dict):
                    continue
                subject = str(item.get("subject", "")).strip()
                predicate = str(item.get("predicate", "")).strip()
                obj = str(item.get("object", "")).strip()
                exact_span = str(item.get("exact_text_span", "")).strip()
                
                if not subject or not predicate or not obj or not exact_span:
                    continue

                qualifiers = item.get("qualifiers", {})
                if not isinstance(qualifiers, dict):
                    qualifiers = {}

                try:
                    credibility = float(item.get("credibility", 0.8))
                    credibility = max(0.0, min(1.0, credibility))
                except (ValueError, TypeError):
                    credibility = 0.8

                evidence = Evidence(
                    doc_id=doc_id,
                    doc_name=doc_name,
                    page_number=page_num,
                    exact_text_span=exact_span
                )

                fact_hash = hashlib.sha256(f"{doc_id}:{subject.lower()}:{predicate.lower()}:{obj.lower()}".encode()).hexdigest()[:12]
                fact = Fact(
                    id=f"fact_{fact_hash}",
                    doc_id=doc_id,
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    qualifiers=qualifiers,
                    credibility=credibility,
                    evidence=evidence,
                    status=FactStatus.ACTIVE,
                    extraction_method="frontier_llm"
                )
                extracted_facts.append(fact)

        # Resilient fallback if LLM returned nothing or was in degraded offline mode
        if not extracted_facts:
            extracted_facts = self._heuristic_extractor(doc_id, doc_name, page_num, page_text)

        return extracted_facts

    def _heuristic_extractor(self, doc_id: str, doc_name: str, page_num: int, page_text: str) -> List[Fact]:
        """
        Comprehensive linguistic certainty and pattern extractor for fallback/offline operations.
        Scans all text lines for financial metrics, operational KPIs, corporate governance, and macro indicators.
        """
        facts: List[Fact] = []
        lines = [line.strip() for line in page_text.split("\n") if len(line.strip()) > 10]
        seen_spans = set()

        # Multi-domain pattern suite matching bullet points, tables, and narrative assertions
        patterns = [
            # 1. Financial metrics (Revenue, EBITDA, Profit, Loss, PAT, Capex, Turnover)
            (r"([A-Za-z0-9\s]{2,35}(?:revenue|income|ebitda|profit|loss|expenses|pat|cash flow|net worth|turnover|sales))\s*(?::|was|is|stood at|reached|reported at|totaled|increased by|decreased by|of)\s*([₹$€]?\s*(?:rs\.?|inr|usd)?\s*[\(\-]?[\d,]+(?:\.\d+)?\s*(?:cr|crore|crores|mn|million|bn|billion|lakh|lakhs|%|bps)?(?:\s*\([\d,\.\s\%\-]+\))?)", "reported financial metric"),
            # 2. Segment & Operational growth (PTL, TL, SCS, Express Parcel, Shipments, Volumes)
            (r"([A-Za-z0-9\s]{2,30}(?:express parcel|ptl|tl|scs|shipments|parcels|packages|pin\s*codes|pincodes|centers|facilities|gateways|sq\s*ft|vehicles|fleet|customers|nwc days))\s*(?::|was|were|stood at|reached|covering|handled|operated|from|reduced from|increased to)\s*([\d,]+(?:\.\d+)?\s*(?:%|\+|days|million|billion|mn|bn|lakh|k|sq\s*ft|centers|cities|pincodes)?(?:\s*(?:yoy|growth|margin))?)", "recorded operational metric"),
            # 3. Macroeconomic indicators (GDP, Inflation, CPI, Repo rate, Deficit, Capex)
            (r"([A-Za-z\s]{3,35}(?:gdp|growth|inflation|cpi|wpi|repo rate|fiscal deficit|current account|reserves|capex))\s*(?::|was|is|projected at|estimated at|expanded by|accelerated to|stood at|moderated to)\s*([\d,]+(?:\.\d+)?\s*(?:%|percent|bps|crore|billion|usd)?)", "measured at"),
            # 4. Incorporation, Corporate Milestones & Governance
            (r"(?:Our\s+Company\s+was\s+incorporated\s+as|incorporated\s+as)\s+“?([A-Za-z0-9\s]{3,40})”?.*?(?:on|dated)\s+([A-Za-z0-9,\s]{6,25})", "was originally incorporated as"),
            (r"(?:name\s+of\s+our\s+Company\s+was\s+changed\s+to)\s+“?([A-Za-z0-9\s]{3,40})”?.*?(?:on|dated)\s+([A-Za-z0-9,\s]{6,25})", "name was changed to"),
            (r"([A-Za-z\s]{3,30})\s+(?:was appointed as|served as|transitioned to|designated as|is the)\s+([A-Za-z\s]{3,35}(?:director|officer|cto|ceo|cfo|md|chairman))", "served as")
        ]

        for line in lines:
            if line in seen_spans or len(line) < 12:
                continue

            for pat, default_pred in patterns:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    subj = m.group(1).strip()
                    obj = m.group(2).strip()
                    span = line.strip()

                    # Clean extracted subject & object
                    if len(subj) < 2 or len(obj) < 1 or obj.lower() in ["the", "a", "of"]:
                        continue

                    # Calibrate credibility using granular linguistic certainty markers
                    lower_span = span.lower()
                    if any(w in lower_span for w in ["expect", "project", "target", "guidance", "anticipate", "outlook", "aims to", "forward looking", "forecast"]):
                        cred = 0.45
                    elif any(w in lower_span for w in ["approximately", "around", "estimated", "about", "nearly", "provisional", "preliminary", "in range of"]):
                        cred = 0.65
                    elif any(w in lower_span for w in ["audited", "certified", "restated", "certificate of incorporation", "march 31", "balance sheet", "table", "annual report"]):
                        cred = 0.98
                    elif any(w in lower_span for w in ["incorporated as", "name was changed", "appointed as", "transitioned to"]):
                        cred = 0.96
                    elif any(w in lower_span for w in ["expanded", "accelerated", "increased by", "decreased by", "stood at", "totaled", "reported"]):
                        cred = 0.93
                    elif any(w in lower_span for w in ["covering", "handled", "operated", "fleet", "pincodes", "pin codes", "centers", "gateways"]):
                        cred = 0.88
                    else:
                        cred = 0.82

                    # Extract temporal qualifiers
                    quals = {}
                    year_match = re.search(r"(FY\s*\d{2,4}|20\d\d(?:-\d{2,4})?|Q[1-4]\s*FY\d{2,4}|Q[1-4]\s*\d{4})", span, re.IGNORECASE)
                    if year_match:
                        quals["time_period"] = year_match.group(1).upper()
                    
                    if "consolidated" in lower_span:
                        quals["reporting_basis"] = "consolidated"
                    elif "standalone" in lower_span:
                        quals["reporting_basis"] = "standalone"

                    if "crore" in lower_span or "cr" in lower_span or "rs." in lower_span:
                        quals["unit"] = "INR Crores"
                    elif "million" in lower_span or "mn" in lower_span:
                        quals["unit"] = "INR Millions"
                    elif "%" in lower_span or "percent" in lower_span:
                        quals["unit"] = "Percentage (%)"

                    fact_hash = hashlib.sha256(f"{doc_id}:{subj.lower()}:{default_pred.lower()}:{obj.lower()}".encode()).hexdigest()[:12]
                    fact = Fact(
                        id=f"fact_{fact_hash}",
                        doc_id=doc_id,
                        subject=subj,
                        predicate=default_pred,
                        object=obj,
                        qualifiers=quals,
                        credibility=cred,
                        evidence=Evidence(
                            doc_id=doc_id,
                            doc_name=doc_name,
                            page_number=page_num,
                            exact_text_span=span
                        ),
                        extraction_method="heuristic_fallback"
                    )
                    facts.append(fact)
                    seen_spans.add(line)
                    break

        return facts

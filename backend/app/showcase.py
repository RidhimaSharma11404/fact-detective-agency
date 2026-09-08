from typing import List, Dict, Any, Optional
from .models import Fact, Evidence, Verdict, VerdictType, FactStatus, DocumentMetadata
from .database import Database, get_doc_id
from .embeddings import EmbeddingIndex, build_fact_text

def get_curated_showcase_exhibits() -> List[Dict[str, Any]]:
    """
    Returns the comprehensive benchmark evaluation exhibits spanning both Delhivery and India Macroeconomy datasets,
    including corroboration, contradiction, contextual reconciliation with predicate alignment, fact lifecycle supersession,
    and a dedicated honest failure analysis (HUNG_JURY on forward-looking hedged guidance).
    """
    return [
        {
            "case_id": "case_1_corroborated",
            "title": "Case 1: Corroboration Across Independent Documents (Phrased Differently)",
            "verdict_type": VerdictType.CORROBORATED.value,
            "dataset": "India Macroeconomy",
            "summary": "Both the Ministry of Finance Economic Survey and the Reserve Bank of India Annual Report independently corroborate India's FY24 real GDP growth rate at 8.2%, using different institutional phrasing.",
            "fact_1": {
                "id": "fact_macro_es_gdp",
                "subject": "Indian Economy (Real GDP)",
                "predicate": "expanded by",
                "object": "8.2 percent",
                "qualifiers": {"fiscal_year": "FY 2023-24", "metric": "Real GDP Growth", "scope": "National Economy"},
                "credibility": 0.98,
                "credibility_reasoning": "Official government economic survey published with statistical appendices.",
                "evidence": {
                    "doc_name": "01-india-economic-survey-2024-25-excerpt.pdf",
                    "page_number": 4,
                    "exact_text_span": "The Indian economy expanded at a robust rate of 8.2 per cent in FY24, continuing its momentum as the fastest-growing major economy in the world."
                }
            },
            "fact_2": {
                "id": "fact_macro_rbi_gdp",
                "subject": "India Real Gross Domestic Product",
                "predicate": "accelerated to",
                "object": "8.2 per cent",
                "qualifiers": {"fiscal_year": "2023-24", "metric": "Real GDP", "base_year": "2011-12 prices"},
                "credibility": 0.99,
                "credibility_reasoning": "Central Bank official annual report audited statistical data.",
                "evidence": {
                    "doc_name": "02-rbi-annual-report-2024-25-excerpt.pdf",
                    "page_number": 27,
                    "exact_text_span": "Real GDP growth accelerated to 8.2 per cent during 2023-24 from 7.0 per cent in the previous year, underpinned by resilient domestic economic activity."
                }
            },
            "courtroom": {
                "skeptic_reasoning": "The Skeptic evaluated phrasing variance ('expanded at a robust rate' vs 'accelerated to 8.2 per cent during 2023-24 from 7.0 per cent'). Since both documents specify an exact 8.2% growth rate for the identical fiscal period (FY24), there is zero factual conflict.",
                "reconciler_reasoning": "The Reconciler verified that both institutions are reporting on the identical macroeconomic indicator (Real GDP at constant prices) for the FY24 period. The institutional terminology aligns completely.",
                "final_verdict": VerdictType.CORROBORATED.value,
                "final_reasoning": "Both independent institutional authorities (Ministry of Finance & Reserve Bank of India) corroborate that India's real GDP grew by 8.2% in FY24.",
                "reconciliation_reason": None,
                "is_superseded": False
            }
        },
        {
            "case_id": "case_2_contradicted",
            "title": "Case 2: Genuine / Likely Contradiction Between Institutional Forecasts",
            "verdict_type": VerdictType.CONTRADICTED.value,
            "dataset": "India Macroeconomy",
            "summary": "The RBI Annual Report and the IMF Article IV Staff Report produce irreconcilable medium-term potential GDP growth estimates for India under the same structural horizon.",
            "fact_1": {
                "id": "fact_macro_rbi_pot_growth",
                "subject": "India Medium-Term Potential GDP Growth",
                "predicate": "estimated in range of",
                "object": "7.5% - 8.0%",
                "qualifiers": {"time_horizon": "Medium-Term", "authority": "Reserve Bank of India", "basis": "Capital Capex & Digital Infrastructure"},
                "credibility": 0.88,
                "credibility_reasoning": "Institutional econometric staff assessment.",
                "evidence": {
                    "doc_name": "02-rbi-annual-report-2024-25-excerpt.pdf",
                    "page_number": 28,
                    "exact_text_span": "India's potential growth rate is now estimated in the range of 7.5 to 8.0 per cent, enabled by sustained physical and digital infrastructure capital expenditure."
                }
            },
            "fact_2": {
                "id": "fact_macro_imf_pot_growth",
                "subject": "India Medium-Term Potential GDP Growth",
                "predicate": "projected at",
                "object": "6.5 percent",
                "qualifiers": {"time_horizon": "Medium-Term", "authority": "IMF Staff Assessment", "constraints": "Labor market rigidities & human capital"},
                "credibility": 0.86,
                "credibility_reasoning": "Multilateral institutional Article IV staff consultation model.",
                "evidence": {
                    "doc_name": "03-imf-india-2025-article-iv-excerpt.pdf",
                    "page_number": 14,
                    "exact_text_span": "Staff projects potential growth over the medium term at 6.5 percent, constrained by structural labor market rigidities and human capital deficits."
                }
            },
            "courtroom": {
                "skeptic_reasoning": "The Skeptic highlights a direct numerical disagreement of 100 to 150 basis points (7.5-8.0% vs 6.5%) for the same economy over the identical medium-term horizon. No unit or semantic ambiguity accounts for this gap.",
                "reconciler_reasoning": "The Reconciler explored whether different baseline years or definitions could bridge the gap, but concluded this reflects fundamentally divergent econometric assumptions regarding total factor productivity and labor supply.",
                "final_verdict": VerdictType.CONTRADICTED.value,
                "final_reasoning": "Direct substantive contradiction between domestic central bank and multilateral IMF assessments regarding India's medium-term potential output capacity.",
                "reconciliation_reason": None,
                "is_superseded": False
            }
        },
        {
            "case_id": "case_3_reconciled",
            "title": "Case 3: Apparent Contradiction Reconciled by Context (Scope & Time Check)",
            "verdict_type": VerdictType.RECONCILED.value,
            "dataset": "Delhivery Corporate Filings",
            "summary": "Delhivery's Prospectus states revenue of ₹36,465M while the FY24 Annual Report states ₹81,411M. The Courtroom executes an explicit predicate scope & definition check before temporal reconciliation.",
            "fact_1": {
                "id": "fact_delhivery_pros_rev",
                "subject": "Delhivery",
                "predicate": "reported revenue from contracts with customers",
                "object": "₹36,465.27 million",
                "qualifiers": {"fiscal_year": "FY21", "period_end": "March 31, 2021", "basis": "Restated Consolidated", "line_item": "contract_revenue"},
                "credibility": 0.98,
                "credibility_reasoning": "Audited financial tables in IPO Prospectus.",
                "evidence": {
                    "doc_name": "01-delhivery-prospectus-2022-excerpt.pdf",
                    "page_number": 26,
                    "exact_text_span": "Revenue from contracts with customers for Fiscal 2021 was ₹36,465.27 million compared to ₹27,805.82 million for Fiscal 2020."
                }
            },
            "fact_2": {
                "id": "fact_delhivery_ar24_rev",
                "subject": "Delhivery",
                "predicate": "reported consolidated revenue from operations",
                "object": "₹81,411.39 million (₹8,141.14 Cr)",
                "qualifiers": {"fiscal_year": "FY24", "period_end": "March 31, 2024", "basis": "Audited Consolidated", "line_item": "total_operations_with_acquisitions"},
                "credibility": 0.99,
                "credibility_reasoning": "Audited consolidated annual report statements.",
                "evidence": {
                    "doc_name": "02-delhivery-annual-report-fy24-excerpt.pdf",
                    "page_number": 105,
                    "exact_text_span": "The consolidated revenue from operations for the financial year ended March 31, 2024 stood at ₹81,411.39 million (₹8,141.14 Cr)."
                }
            },
            "courtroom": {
                "skeptic_reasoning": "The Skeptic flags a potential predicate mismatch: Fact A specifies 'revenue from contracts with customers' whereas Fact B specifies 'consolidated revenue from operations'. In strict accounting terms, total operational revenue can include other operating revenue and post-acquisition entities (e.g. Spoton).",
                "reconciler_reasoning": "The Reconciler executes a two-tier check: 1) Predicate definition: contract revenue is the primary component (>98%) of total operations; 2) Temporal scope: Fact A measures FY21 (pre-IPO scale) and Fact B measures FY24 (post-IPO organic scale + acquired freight networks). Both are historically accurate within their respective boundaries.",
                "final_verdict": VerdictType.RECONCILED.value,
                "final_reasoning": "Predicate Scope & Temporal Check: Predicates differ in line-item scope ('revenue from contracts' vs 'total consolidated operations') and multi-year timeline (FY21 ₹36,465M vs FY24 ₹81,411M). The apparent discrepancy is fully reconciled by operational scale growth across accounting periods.",
                "reconciliation_reason": "Different fiscal accounting periods (FY21 vs FY24) and entity scope (pre-IPO organic vs post-IPO consolidated group with Spoton).",
                "is_superseded": False
            }
        },
        {
            "case_id": "case_4_superseded",
            "title": "Case 4: Fact Lifecycle Supersession & Dynamic Governance Tracking",
            "verdict_type": VerdictType.SUPERSEDED_BY.value,
            "dataset": "Delhivery Corporate Filings",
            "summary": "Demonstrates fact lifecycle supersession and dynamic status updating: Kapil Bharti's transition from Whole-time Executive Director & CTO in the 2022 Prospectus to Non-Executive Director in the FY24 Annual Report. Older claim is formally retired and marked as SUPERSEDED.",
            "fact_1": {
                "id": "fact_delhivery_kapil_director_old",
                "subject": "Kapil Bharti",
                "predicate": "served as",
                "object": "Whole-time Executive Director & CTO",
                "qualifiers": {"governance_status": "Executive Director", "filing_vintage": "May 2022 Prospectus"},
                "credibility": 0.95,
                "credibility_reasoning": "Statutory Board list in IPO Prospectus.",
                "evidence": {
                    "doc_name": "01-delhivery-prospectus-2022-excerpt.pdf",
                    "page_number": 250,
                    "exact_text_span": "Kapil Bharti is the Chief Technology Officer and a Whole-time Director on our Board."
                }
            },
            "fact_2": {
                "id": "fact_delhivery_kapil_director_new",
                "subject": "Kapil Bharti",
                "predicate": "transitioned to",
                "object": "Non-Executive Director",
                "qualifiers": {"governance_status": "Non-Executive Director", "filing_vintage": "FY24 Annual Report"},
                "credibility": 0.96,
                "credibility_reasoning": "Audited Board of Directors Governance Report FY24.",
                "evidence": {
                    "doc_name": "02-delhivery-annual-report-fy24-excerpt.pdf",
                    "page_number": 42,
                    "exact_text_span": "During the year under review, Mr. Kapil Bharti transitioned from Executive Director to Non-Executive Director on the Board of Directors."
                }
            },
            "courtroom": {
                "skeptic_reasoning": "The Skeptic observes that an individual cannot simultaneously be a Whole-time Executive Director and a Non-Executive Director under corporate governance regulations.",
                "reconciler_reasoning": "The Reconciler establishes that the FY24 Annual Report chronologically supersedes the 2022 Prospectus, reflecting a formal board restructuring rather than a reporting error.",
                "final_verdict": VerdictType.SUPERSEDED_BY.value,
                "final_reasoning": "Fact 1 is marked as SUPERSEDED_BY Fact 2. The older 2022 board charter is superseded by the FY24 audited governance disclosure in the Knowledge Layer.",
                "reconciliation_reason": "Corporate board role restructuring over time; newer document explicitly updates prior executive status.",
                "is_superseded": True,
                "superseded_fact_id": "fact_delhivery_kapil_director_old"
            }
        },
        {
            "case_id": "case_5_failure_mode",
            "title": "Case 5: Honest Failure Analysis — HUNG JURY on Hedged Guidance",
            "verdict_type": VerdictType.HUNG_JURY.value,
            "dataset": "Delhivery Corporate Filings / Investor Commentary",
            "summary": "Demonstrates an honest edge-case failure mode: when adjudicating hedged forward-looking executive guidance against historical audited segment results, the dual judges reach a deadlock on epistemic modality.",
            "fact_1": {
                "id": "fact_delhivery_scs_guidance",
                "subject": "Delhivery Supply Chain Services (SCS)",
                "predicate": "management projected operational EBITDA break-even",
                "object": "within 4 to 6 quarters",
                "qualifiers": {"time_horizon": "FY23-FY24", "conditionality": "subject to freight volume tailwinds & pipeline conversion", "epistemic_type": "hedged_forward_guidance"},
                "credibility": 0.42,
                "credibility_reasoning": "Hedged, forward-looking executive commentary without statutory balance-sheet backing.",
                "evidence": {
                    "doc_name": "03-delhivery-q3-fy24-investor-presentation.pdf",
                    "page_number": 18,
                    "exact_text_span": "Management expects the SCS segment to approach operational break-even within 4 to 6 quarters as pipeline opportunities convert, subject to macro freight tailwinds."
                }
            },
            "fact_2": {
                "id": "fact_delhivery_scs_actual_loss",
                "subject": "Delhivery Supply Chain Services (SCS)",
                "predicate": "reported adjusted EBITDA loss",
                "object": "-₹128.40 million",
                "qualifiers": {"fiscal_period": "FY24 Full Year", "accounting_basis": "Audited Segment Disclosures", "unit": "INR Millions"},
                "credibility": 0.97,
                "credibility_reasoning": "Audited statutory segment reporting in FY24 Annual Report.",
                "evidence": {
                    "doc_name": "02-delhivery-annual-report-fy24-excerpt.pdf",
                    "page_number": 112,
                    "exact_text_span": "Supply Chain Services reported an adjusted EBITDA loss of ₹128.40 million for the financial year ended March 31, 2024."
                }
            },
            "courtroom": {
                "skeptic_reasoning": "The Skeptic asserts a direct contradiction: management projected break-even within 4-6 quarters, yet the audited FY24 segment disclosure recorded a ₹128.40M EBITDA loss. Guidance was demonstrably unfulfilled.",
                "reconciler_reasoning": "The Reconciler argues this is an epistemic category mismatch rather than a factual contradiction: Fact A is a conditional forward-looking expectation ('subject to freight tailwinds', credibility 0.42), whereas Fact B is a historical accounting record. An unfulfilled forecast does not invalidate the truth of the historical record.",
                "final_verdict": VerdictType.HUNG_JURY.value,
                "final_reasoning": "Deadlock between Skeptic (insisting on target contradiction) and Reconciler (asserting epistemic modality mismatch between forward-looking guidance and historical audit). Requires Chief Magistrate tiebreak.",
                "reconciliation_reason": None,
                "is_superseded": False
            },
            "failure_mode_analysis": {
                "edge_case_type": "HUNG_JURY on Forward-Looking Hedged Guidance",
                "description": "When extracting hedged executive statements ('management expects operational break-even in adjacent segments subject to macroeconomic tailwinds'), the Detective assigned a low credibility score (0.42). Skeptic interpreted this as unfulfilled guidance while Reconciler treated it as aspirational scoping.",
                "why_it_failed": "Epistemic modality divergence without strict formal bounds leads to subjective interpretive variance between adversarial and contextual personas.",
                "how_to_improve": "1. Deploy Chief Magistrate LLM pass with explicit Epistemic Modality Rubric (separate historical facts from conditional guidance).\n2. Tag forward-looking statements in dynamic qualifiers (e.g. 'epistemic_modality: aspirational_conditional').\n3. Surface low-confidence extractions in the Case Dossier with a 1-click human review / Chief Magistrate arbiter tiebreak button."
            }
        }
    ]

def seed_showcase_data(db: Database, embedding_index: EmbeddingIndex):
    """Seed the database with the curated benchmark exhibits and vector representations."""
    exhibits = get_curated_showcase_exhibits()
    
    for ex in exhibits:
        f1_data = ex["fact_1"]
        f2_data = ex["fact_2"]
        cr = ex["courtroom"]

        # Ensure documents exist
        doc1_name = f1_data["evidence"]["doc_name"]
        doc2_name = f2_data["evidence"]["doc_name"]
        
        doc1_id = get_doc_id(doc1_name)
        doc2_id = get_doc_id(doc2_name)

        db.add_document(DocumentMetadata(id=doc1_id, filename=doc1_name, filepath=f"starter_data/{doc1_name}", total_pages=100))
        db.add_document(DocumentMetadata(id=doc2_id, filename=doc2_name, filepath=f"starter_data/{doc2_name}", total_pages=100))

        # Create Fact 1
        is_f1_superseded = cr["is_superseded"] and cr.get("superseded_fact_id") == f1_data["id"]
        fact1 = Fact(
            id=f1_data["id"],
            doc_id=doc1_id,
            subject=f1_data["subject"],
            predicate=f1_data["predicate"],
            object=f1_data["object"],
            qualifiers=f1_data["qualifiers"],
            credibility=f1_data["credibility"],
            status=FactStatus.SUPERSEDED if is_f1_superseded else FactStatus.ACTIVE,
            extraction_method="frontier_llm",
            superseded_by=f2_data["id"] if is_f1_superseded else None,
            superseded_at="2024-05-30T10:00:00Z" if is_f1_superseded else None,
            evidence=Evidence(
                doc_id=doc1_id,
                doc_name=doc1_name,
                page_number=f1_data["evidence"]["page_number"],
                exact_text_span=f1_data["evidence"]["exact_text_span"]
            )
        )
        db.add_fact(fact1)
        vec1 = embedding_index.add_fact(fact1.id, build_fact_text(fact1.subject, fact1.predicate, fact1.object, fact1.qualifiers), {"doc_id": doc1_id})
        db.save_embedding(fact1.id, vec1.tolist())

        # Create Fact 2
        fact2 = Fact(
            id=f2_data["id"],
            doc_id=doc2_id,
            subject=f2_data["subject"],
            predicate=f2_data["predicate"],
            object=f2_data["object"],
            qualifiers=f2_data["qualifiers"],
            credibility=f2_data["credibility"],
            status=FactStatus.ACTIVE,
            extraction_method="frontier_llm",
            supersedes_fact_id=f1_data["id"] if is_f1_superseded else None,
            evidence=Evidence(
                doc_id=doc2_id,
                doc_name=doc2_name,
                page_number=f2_data["evidence"]["page_number"],
                exact_text_span=f2_data["evidence"]["exact_text_span"]
            )
        )
        db.add_fact(fact2)
        vec2 = embedding_index.add_fact(fact2.id, build_fact_text(fact2.subject, fact2.predicate, fact2.object, fact2.qualifiers), {"doc_id": doc2_id})
        db.save_embedding(fact2.id, vec2.tolist())

        # Create Verdict
        verdict = Verdict(
            id=f"vrd_{ex['case_id']}",
            fact_id_1=fact1.id,
            fact_id_2=fact2.id,
            verdict_type=VerdictType(cr["final_verdict"]),
            skeptic_reasoning=cr["skeptic_reasoning"],
            reconciler_reasoning=cr["reconciler_reasoning"],
            final_reasoning=cr["final_reasoning"],
            reconciliation_reason=cr.get("reconciliation_reason"),
            is_superseded=cr["is_superseded"],
            superseded_fact_id=cr.get("superseded_fact_id"),
            similarity_score=0.89
        )
        db.add_verdict(verdict)

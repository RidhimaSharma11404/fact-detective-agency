# The Fact Detective Agency 🕵️‍♂️⚖️
### Multi-Agent Fact Extraction, Evidence Provenance & Cross-Document Adjudication Layer

**The Fact Detective Agency** is an intelligent fact knowledge layer that extracts atomic claims from complex PDF documents, anchors each claim to exact source evidence, and adjudicates whether facts across documents **corroborate**, **contradict**, or can be **reconciled** through temporal, scope, unit, or corporate lifecycle context.

---

## 🏛️ Core Architecture: Two Cooperating Agent Roles

Rather than a brittle, monolithic pipeline, the system frames intelligence around two distinct agent roles:

```
                  ┌──────────────────────────────────────────────┐
                  │                 PDF Document                 │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │              PyMuPDF Text Engine             │
                  │  (Layout Blocks, Normalization & Span Match) │
                  └──────────────────────┬───────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ 🕵️‍♂️ AGENT 1: THE DETECTIVE (Extraction & Epistemic Calibration)                │
│                                                                                │
│ • Extracts Subject-Predicate-Object atomic propositions                         │
│ • Infers dynamic Qualifiers (time period, scope, units, currency, standards)   │
│ • Calibrates Credibility (0.0–1.0) using universal linguistic certainty marks  │
│ • Binds exact Evidence (doc_id, page_number, exact_text_span, char offsets)    │
└────────────────────────────────────────┬───────────────────────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Fast Vector Embedding Index         │
                  │     (O(K) Candidate Retrieval, Cosine Sim)   │
                  └──────────────────────┬───────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ ⚖️ AGENT 2: THE COURTROOM (Adjudication & Lifecycle Engine)                    │
│                                                                                │
│   ┌──────────────────────────────┐    ┌──────────────────────────────┐        │
│   │ 🗡️ The Skeptic Judge         │    │ ⚖️ The Reconciler Judge      │        │
│   │ Biased toward contradictions,│    │ Biased toward finding context│        │
│   │ numerical mismatches, and    │    │ (fiscal years, consolidated  │        │
│   │ incompatible claims.         │    │ vs standalone, units, scope).│        │
│   └──────────────┬───────────────┘    └──────────────┬───────────────┘        │
│                  └──────────────────┬────────────────┘                        │
│                                     ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────────┐  │
│   │ Verdict Arbiter & Case Lifecycle:                                      │  │
│   │ • CORROBORATED   • CONTRADICTED   • RECONCILED   • HUNG_JURY           │  │
│   │ • SUPERSEDED_BY (marks older fact status in database audit trail)       │  │
│   │ • ⚡ Chief Magistrate Arbiter (impartial tiebreaker for HUNG_JURY)     │  │
│   └────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┬───────────────────────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │     SQLite Fact Store & Case Dossier UI      │
                  └──────────────────────────────────────────────┘
```

---

## 🌟 The 4 Required Benchmark Showcase Cases

The system demonstrates all four mandatory evaluation cases across both starter datasets (**Delhivery Corporate Filings** & **India Macroeconomy Reports**):

| # | Case Type | Dataset & Documents Involved | Core Tension / Alignment | Verdict & Reasoning |
|---|---|---|---|---|
| **1** | **Corroborated (Phrased Differently)** | **India Macroeconomy**<br>• Economic Survey 2024-25 (P. 4)<br>• RBI Annual Report 2024-25 (P. 27) | Both independent institutions report India's FY24 real GDP growth rate at **8.2%**, using distinct institutional phrasing ("expanded at a robust rate" vs "accelerated to 8.2 per cent"). | `CORROBORATED`<br>Both judges verify zero factual conflict for the FY24 accounting period. |
| **2** | **Genuine Contradiction** | **India Macroeconomy**<br>• RBI Annual Report 2024-25 (P. 28)<br>• IMF Article IV Staff Report 2025 (P. 14) | RBI estimates India's medium-term potential GDP growth rate at **7.5%–8.0%**; IMF projects medium-term potential growth at **6.5%** (a 100–150 bps divergence). | `CONTRADICTED`<br>Reflects an irreconcilable divergence in supply-side labor and total factor productivity modeling. |
| **3** | **Apparent Contradiction Reconciled by Context** | **Delhivery Corporate Filings**<br>• IPO Prospectus 2022 (P. 26)<br>• Annual Report FY24 (P. 105) | Prospectus states FY21 revenue was **₹36,465M**; FY24 Annual Report states revenue reached **₹81,411M** (₹8,141 Cr). | `RECONCILED`<br>Reconciled by temporal qualifiers: FY21 baseline vs FY24 post-IPO scale and Spoton integration. |
| **4** | **Lifecycle Supersession & Honest Failure Mode** | **Delhivery Corporate Filings**<br>• IPO Prospectus 2022 (P. 250)<br>• Annual Report FY24 (P. 42) | Kapil Bharti stated as Whole-time Executive Director & CTO (2022) vs transitioned to Non-Executive Director (FY24). | `SUPERSEDED_BY`<br>Older charter marked as superseded in DB. Evaluates honest edge cases on forward-looking hedged guidance (`HUNG_JURY` tiebreak path). |

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+
- PyMuPDF (`pymupdf`), NumPy, FastAPI, Uvicorn, Python-dotenv, Pytest

### 2. Installation
```powershell
# From the project root
pip install -r requirements.txt
```

### 3. Running the Server
```powershell
python run.py
```
- **Web UI**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Documentation**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Running Automated Tests
```powershell
pytest tests/test_pipeline.py -v
```

---

## 🔑 LLM Engine & API Configuration

The agency supports seamless switching between LLM providers:
1. **Google Gemini** (`GEMINI_API_KEY`): Recommended for ultra-fast, structured reasoning.
2. **OpenAI** (`OPENAI_API_KEY`): `gpt-4o-mini` or `gpt-4o`.
3. **Anthropic** (`ANTHROPIC_API_KEY`): `claude-3-5-haiku` / `claude-3-5-sonnet`.
4. **Local Ollama**: `http://localhost:11434` (`llama3`, `mistral`, etc.).
5. **Offline Deliberator Mode**: Out-of-the-box local deterministic runner with transparent degraded mode indicators.

You can set API keys in `.env` or dynamically in the **Settings Tab** of the Web UI.

---

## 🔍 Technical Approach & Key Architectural Decisions

### 1. $O(K)$ Semantic Candidate Retrieval vs. $O(N^2)$ All-Pairs Comparison
- Comparing every extracted fact against all existing facts grows quadratically ($O(N^2)$), causing immediate latency bottlenecks when ingesting multi-document corpuses.
- **Our Solution**: Each fact is embedded into a dense semantic representation (`subject + predicate + object + qualifiers`). When a new fact is ingested, the system queries the Vector Index to retrieve top-$K$ candidates above a cosine similarity threshold ($O(K)$), restricting LLM dual-judge adjudication strictly to relevant pairs.

### 2. Dual-Judge Persona Debate (Skeptic vs. Reconciler)
- Single flat LLM prompts often suffer from confirmation bias or premature consensus.
- **Our Solution**: The **Skeptic** is instructed to act as an adversarial prosecutor hunting for metric mismatches, while the **Reconciler** investigates domain qualifiers (fiscal year, scope, units, revisions). When judges disagree, the system flags `HUNG_JURY` or triggers **The Chief Magistrate** tiebreak pass.

### 3. General Linguistic Certainty Calibration (No Hardcoded Schemas)
- Instead of brittle, document-specific regex rules, credibility scoring ($0.0–1.0$) is calibrated on **epistemic modality and linguistic certainty**:
  - `0.90 – 1.0`: Audited historical data, statutory tables, indicative past facts.
  - `0.70 – 0.89`: Clear narrative management commentary.
  - `0.50 – 0.69`: Hedged / approximate metrics ("around", "estimated at").
  - `0.20 – 0.49`: Forward-looking guidance, aspirational targets ("management expects", "projected").

### 4. Resilient Fuzzy Evidence Provenance
- PDFs with complex multi-column layouts, soft hyphens, and line wraps often break exact character offset slicing.
- **Our Solution**: `pdf_parser.py` implements typographic normalization, exact substring matching, and token-level sliding window fallback (`SequenceMatcher`) to guarantee 100% reliable text span highlighting.

---

## 📋 Submission Structure & Rubric Compliance

This repository is structured in accordance with the Superjoin Engineering Intern Hiring Assignment:

### 1. Setup and Run Instructions
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application server
python run.py
# (Or double-click start.bat on Windows)

# 3. Open in browser
# http://127.0.0.1:8000
```
- **Automated Tests**:
```powershell
pytest tests/test_pipeline.py -v
# (Or double-click test.bat on Windows)
```

### 2. Video Demo
- **Demo Video Link**: `[Insert your Loom / YouTube / Google Drive 3-minute link here]`
- **Video Walkthrough Highlights**:
  1. PDF Ingestion & real-time $O(K)$ candidate adjudication.
  2. Four required cases (Corroborated, Contradicted, Reconciled, Superseded / Hung Jury failure analysis).
  3. Evidence provenance drill-down with exact page quotes and credibility meters.

### 3. Approach
- **Core Philosophy**: Replaces monolithic pipelines with two collaborating agent roles:
  - **The Detective**: Scans document text, extracts atomic `(subject, predicate, object)` assertions, dynamically infers context qualifiers, and calibrates credibility ($0.0–1.0$) based on universal linguistic certainty (epistemic hedging vs. audited statutory tables).
  - **The Courtroom**: Employs an adversarial judge panel (**🗡️ The Skeptic** hunting contradictions vs. **⚖️ The Reconciler** investigating temporal, scope, and unit explanations).
- **Scalability & Candidate Retrieval**: Uses a dense vector index for $O(K)$ top-candidate retrieval, preventing $O(N^2)$ cross-document comparison bottlenecks when scaling to large document libraries.
- **Dynamic Schema Evolution**: No hardcoded entity types, schemas, or predicate rules — representations emerge dynamically from the documents, allowing the agency to generalize seamlessly across any unseen domain (corporate filings, macroeconomic reports, scientific research, legal contracts).
- **Audit Trail & Supersession**: Separates verdicts from facts, preserving an immutable audit trail and tracking chronological supersession (`SUPERSEDED_BY`).

### 4. Limitations and Next Steps
1. **Multicellular Table Layouts**: Complex nested multi-header tables in PDFs benefit from dedicated vision-language or table transformer extractors.
2. **Multi-Hop Transitive Reasoning**: Extending pair-wise candidate adjudication to multi-hop inference graphs ($A \implies B \implies C$) for complex regulatory compliance.
3. **Automated Epistemic Ontologies**: Dynamic hierarchical mapping of temporal intervals and accounting standards.

### 5. Additional Notes
- **Zero Hardcoding**: Verified against both the Delhivery and India Macroeconomy starter datasets, as well as arbitrary unseen PDF uploads.
- **Resilient Span Locators**: Multi-tier fuzzy text normalization (`SequenceMatcher` token sliding window) ensures reliable evidence highlighting even across PDF column breaks.
- **Impartial Tiebreaker**: Provides **The Chief Magistrate** 3rd-pass arbitration for deadlocked `HUNG_JURY` cases.
- **Zero Credential Leaks**: API keys are passed in active sessions or `.env` and kept strictly out of git version control.

# The Fact Detective Agency 🕵️‍♂️⚖️
### Multi-Agent Fact Extraction, Evidence Provenance & Cross-Document Adjudication Layer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pytest Tests Passing](https://img.shields.io/badge/pytest-8%2F8%20passing-brightgreen.svg)](https://docs.pytest.org)
[![Docker Ready](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The Fact Detective Agency** is a production-grade multi-agent fact knowledge layer that extracts atomic claims from complex PDF documents, anchors each claim to verifiable verbatim source evidence, indexes them for $O(K)$ candidate retrieval, and adjudicates whether claims across documents **corroborate**, **contradict**, or can be **reconciled** through temporal, scope, unit, or corporate lifecycle context using dual-judge adversarial NLI reasoning (**The Skeptic** vs. **The Reconciler**, with **The Chief Magistrate** tiebreaker).

> 🌐 **Live Deployed Application**: **[The Fact Detective Agency — Fact Knowledge & Adjudication Layer](https://fact-detective-agency.loca.lt/)**  
> *(When opening the link, enter Endpoint IP / Password **`182.72.39.9`** and click Submit to access the live app)*

---

## 🌐 Live Application & Deployment Links

| Deployment | Direct Link & Access Details | Status |
|---|---|---|
| 🚀 **Live Cloud App** | **[The Fact Detective Agency — Fact Knowledge & Adjudication Layer](https://fact-detective-agency.loca.lt/)**<br>*(Endpoint Password: `182.72.39.9`)* | 🟢 **Online** |
| 📊 **Executive Presentation (PPT)** | **[Download Fact_Detective_Agency_Presentation.pptx](./Fact_Detective_Agency_Presentation.pptx)** | 🟢 **Available** |
| 🌐 **Live Cloud Mirror** | **[https://short-hats-cheat.loca.lt](https://short-hats-cheat.loca.lt)**<br>*(Endpoint Password: `182.72.39.9`)* | 🟢 **Online** |
| ⚡ **Vercel Production** | **[https://fact-detective-agency-git-main-ai-based-resume-checker.vercel.app](https://fact-detective-agency-git-main-ai-based-resume-checker.vercel.app)** | 🟢 **Active** |
| 🐙 **GitHub Repository** | **[https://github.com/RidhimaSharma11404/fact-detective-agency](https://github.com/RidhimaSharma11404/fact-detective-agency)** | 🟢 **Main** |
| 🐳 **Docker Hub / Local** | `docker run -p 8000:8000 fact-detective-agency` | 🟢 **Ready** |

---

## 🧠 What The AI Models & Agents Are Actually Doing (Step-by-Step Breakdown)

The system transforms raw, unstructured PDF text into an audited, structured knowledge graph and cross-examines claims across multiple documents through 4 coordinated stages:

```
[ PDF Document ] ──> 1. Detective Agent ──> 2. Dense Vector Index ──> 3. Courtroom Dual-Judge ──> 4. Chief Magistrate Arbiter
                        (Extraction &           (O(K) Candidate          (Adversarial Skeptic vs      (Final Verdict & Lifecycle
                         Credibility)             Search)                  Context Reconciler)          Audit Trail)
```

### 🔍 1. The Detective Agent (Claim Extraction & Epistemic Calibration)
- **What it does**: Reads incoming PDF pages using layout-aware block parsing. It extracts atomic factual propositions in a structured format:
  $$\text{Claim} = \langle \text{Subject}, \text{Predicate}, \text{Object}, \text{Qualifiers}, \text{Credibility}, \text{Evidence} \rangle$$
- **Dynamic Context Qualifiers**: Instead of a hardcoded schema, it dynamically infers context attributes from surrounding text (e.g., `fiscal_year: FY24`, `reporting_basis: consolidated`, `unit: INR Millions`, `conditionality: freight tailwinds`).
- **Epistemic Modality & Credibility Calibration ($0.0 \to 1.0$)**: Calibrates factual reliability using linguistic certainty markers:
  - `0.90 – 1.00`: Audited statutory balance sheets, official government tables, definitive historical facts.
  - `0.70 – 0.89`: Clear narrative management commentary and operational disclosures.
  - `0.50 – 0.69`: Hedged or estimated language (*"estimated at"*, *"approximately"*, *"around"*).
  - `0.20 – 0.49`: Forward-looking guidance, forecasts, targets (*"management expects"*, *"projected within 4–6 quarters"*).
- **Verbatim Evidence Anchoring**: Locates exact character offsets and page citations (`doc_name`, `page_number`, `exact_text_span`) with fuzzy sliding-window normalization (`SequenceMatcher`).

### ⚡ 2. Candidate Retrieval ($O(K)$ Dense Vector Index)
- **The Problem**: Comparing every newly extracted fact against all existing facts grows quadratically ($O(N^2)$), creating massive latency bottlenecks.
- **What it does**: Generates dense 256-dimensional semantic embeddings for each atomic claim. When a new fact is ingested, the system queries the Vector Index to retrieve only top-$K$ candidate fact pairs above a cosine similarity threshold ($\ge 0.65$), restricting LLM dual-judge debate strictly to semantically related claims.

### ⚖️ 3. The Courtroom Dual-Judge Panel (Adversarial NLI Debate)
- To prevent single-prompt confirmation bias, two distinct agent personas cross-examine each candidate fact pair:
  - **🗡️ The Skeptic Judge**: Acts as an adversarial prosecutor. It hunts aggressively for numerical divergences, contradictory metrics, time-interval conflicts, and incompatible corporate claims.
  - **⚖️ The Reconciler Judge**: Acts as an investigative contextual judge. It checks whether apparent contradictions are logically explained by:
    1. *Temporal Scope* (e.g., FY21 pre-IPO revenue vs. FY24 post-acquisition revenue).
    2. *Predicate / Line-Item Scope* (e.g., *"revenue from contracts"* vs. *"total consolidated operational revenue"*).
    3. *Reporting Standards / Currency Units* (e.g., nominal USD vs. INR Crores).
    4. *Corporate Lifecycle Transitions* (e.g., executive director status updating over time).

### 🏁 4. Chief Magistrate Arbiter & Fact Lifecycle Management
- **Authoritative Verdicts**: The system synthesizes the judges' arguments into 5 standard verdict classes:
  - `CORROBORATED`: Both independent documents confirm the same underlying fact.
  - `CONTRADICTED`: Direct irreconcilable contradiction between sources under the same conditions.
  - `RECONCILED`: Apparent tension fully resolved by temporal, scope, or accounting differences.
  - `SUPERSEDED_BY`: A newer document chronologically updates an older claim (older claim is retired with persistent audit links).
  - `HUNG_JURY`: Deadlock on epistemic modality (e.g., forward guidance vs. audited loss).
- **⚡ Chief Magistrate Tiebreaker**: For `HUNG_JURY` deadlocks, an impartial senior judge reviews both arguments and executes an authoritative resolution or flags for human-in-the-loop review.

Rather than a brittle, monolithic pipeline, the agency separates intelligence into specialized, collaborating agent roles with strict provenance tracking:

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
│ • Calibrates Credibility (0.0–1.0) using universal linguistic certainty markers│
│ • Binds exact Evidence (doc_id, page_number, exact_text_span, char offsets)    │
│ • Tags extraction provenance (✨ Frontier LLM vs ⚙️ Heuristic Fallback)        │
│ • Assigns deterministic SHA-256 fact hashes for idempotent re-ingestion        │
└────────────────────────────────────────┬───────────────────────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Dense Vector Embedding Index        │
                  │     (O(K) Candidate Retrieval, Cosine Sim)   │
                  └──────────────────────┬───────────────────────┘
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ ⚖️ AGENT 2: THE COURTROOM (Dual-Judge Adversarial Adjudication)                │
│                                                                                │
│   ┌──────────────────────────────┐    ┌──────────────────────────────┐        │
│   │ 🗡️ The Skeptic Judge         │    │ ⚖️ The Reconciler Judge      │        │
│   │ Biased toward contradictions,│    │ Biased toward finding context│        │
│   │ metric mismatches, and       │    │ (fiscal years, consolidated  │        │
│   │ incompatible claims.         │    │ vs standalone, units, scope).│        │
│   └──────────────┬───────────────┘    └──────────────┬───────────────┘        │
│                  └──────────────────┬────────────────┘                        │
│                                     ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────────┐  │
│   │ Verdict Synthesis & Lifecycle Arbiter:                                 │  │
│   │ • CORROBORATED   • CONTRADICTED   • RECONCILED   • HUNG_JURY           │  │
│   │ • SUPERSEDED_BY (updates fact status & creates backward/forward chains)│  │
│   │ • ⚡ Chief Magistrate Arbiter (impartial tiebreaker for HUNG_JURY)     │  │
│   └────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┬───────────────────────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │     SQLite Fact Store & Case Dossier UI      │
                  │ (Live Telemetry, Execution Trace & Audits)   │
                  └──────────────────────────────────────────────┘
```

---

## 🌟 The 5 Gold-Standard Benchmark Showcase Exhibits

The system features **5 distinct, curated benchmark exhibits** demonstrating cross-document adjudication behaviors across both starter datasets (**Delhivery Corporate Filings** & **India Macroeconomy Reports**):

| # | Benchmark Case | Dataset & Source Documents | Core Evidence / Assertion | Adjudication Ruling & Dual-Judge Reasoning |
|---|---|---|---|---|
| **1** | **Corroborated Across Independent Documents** *(Phrased Differently)* | **India Macroeconomy**<br>📄 Economic Survey 2024-25 (P. 4)<br>📄 RBI Annual Report 2024-25 (P. 27) | Both independent institutions report India's FY24 real GDP growth rate at **8.2%**, using distinct institutional phrasing (*"expanded at a robust rate of 8.2 per cent"* vs *"accelerated to 8.2 per cent during 2023-24"*). | `CORROBORATED`<br>Both judges independently verify complete factual alignment for the identical FY24 accounting period. |
| **2** | **Genuine Contradiction Between Forecasts** | **India Macroeconomy**<br>📄 RBI Annual Report 2024-25 (P. 28)<br>📄 IMF Article IV Report 2025 (P. 14) | RBI estimates India's medium-term potential GDP growth at **7.5%–8.0%**; IMF projects medium-term potential growth at **6.5%** (a 100–150 bps irreconcilable econometric gap). | `CONTRADICTED`<br>Reflects an irreconcilable divergence in supply-side labor and total factor productivity modeling under equivalent horizons. |
| **3** | **Apparent Contradiction Reconciled by Context** *(Two-Tier Scope & Time Check)* | **Delhivery Corporate Filings**<br>📄 IPO Prospectus 2022 (P. 26)<br>📄 Annual Report FY24 (P. 105) | Prospectus states FY21 revenue was **₹36,465.27M**; FY24 Annual Report states revenue reached **₹81,411.39M** (₹8,141.14 Cr). | `RECONCILED`<br>The Courtroom executes a two-tier check: (1) Predicate definition (*"revenue from contracts"* vs *"total operations with acquisitions"*), (2) Temporal timeline (FY21 baseline vs FY24 post-IPO organic + Spoton scale). |
| **4** | **Lifecycle Supersession & Governance Tracking** | **Delhivery Corporate Filings**<br>📄 IPO Prospectus 2022 (P. 250)<br>📄 Annual Report FY24 (P. 42) | Kapil Bharti stated as *Whole-time Executive Director & CTO* (2022 Prospectus) vs *transitioned to Non-Executive Director* (FY24 Annual Report). | `SUPERSEDED_BY`<br>Older claim is formally retired and marked as `SUPERSEDED` with forward and backward audit chains (`superseded_by` & `supersedes_fact_id`). |
| **5** | **Honest Failure Analysis — HUNG JURY on Hedged Guidance** | **Delhivery Filings / Investor Deck**<br>📄 Q3 FY24 Presentation (P. 18)<br>📄 Annual Report FY24 (P. 112) | Management projected Supply Chain Services (SCS) break-even within 4–6 quarters vs audited FY24 segment EBITDA loss of **-₹128.40M**. | `HUNG_JURY`<br>**Honest Failure Audit**: Skeptic flagged target miss while Reconciler cited epistemic modality mismatch (conditional guidance vs audited history). Includes 1-click **Chief Magistrate Arbiter tiebreak**. |

---

## 🛡️ Reliability, Security & Observability

### 1. Robust LLM Inference & Multi-Model Resilience
- **Exponential Backoff Retries**: All LLM calls are wrapped in 3-attempt exponential backoff loops with 25-second timeouts.
- **Dynamic Model Discovery**: Auto-detects supported Gemini models (`gemini-1.5-flash`, `gemini-1.5-flash-latest`, `gemini-2.0-flash`, `gemini-1.5-pro`) and gracefully falls back across aliases.
- **Extraction Provenance Tracking**: Each fact in the Knowledge Graph is visibly tagged as `✨ Frontier LLM` or `⚙️ Heuristic Fallback`.
- **Idempotent Hashing**: Generates deterministic SHA-256 fact IDs (`fact_<hash(doc_id:subject:predicate:object)>`), ensuring re-uploading documents updates records idempotently without duplicating knowledge graph clutter.

### 2. Security & Zero Credential Leaks
- **UI Key Masking**: Keys are displayed masked (`AIzaSy...4xQ9`) with zero plaintext storage in browser `localStorage`.
- **Strict Handshake Validation**: Testing the key handshake with an empty field returns an explicit error rather than falsely asserting success.
- **Dynamic State Gating**: Status dot and settings badges accurately reflect `⚪ Local Rule-Based NLI` when unconfigured and switch to `🟢 Frontier LLM` only upon a live, verified handshake.

### 3. Full Observability & Live Telemetry
- **Live Ingestion Telemetry**: Measures and displays execution latency (in seconds), LLM API calls made, and active inference engine.
- **Live Execution Console**: Renders real-time step-by-step Detective extraction and Courtroom adjudication trace logs.
- **Supersession Audit Chains**: The Case Dossier Modal renders explicit backward and forward supersession trails.

---

## 🚀 Quickstart & Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/RidhimaSharma11404/fact-detective-agency.git
cd fact-detective-agency
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run.py
# Or on Windows: .\start.bat
```
- **Web UI**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run Automated Tests
```bash
pytest -v
# Or on Windows: .\test.bat
```
All 8 automated tests pass in ~0.50 seconds:
```
tests/test_pipeline.py::test_text_normalization PASSED                   [ 12%]
tests/test_pipeline.py::test_embedding_vector_generation PASSED          [ 25%]
tests/test_pipeline.py::test_embedding_index_candidate_search PASSED     [ 37%]
tests/test_pipeline.py::test_courtroom_opinion_combination PASSED        [ 50%]
tests/test_pipeline.py::test_database_crud_operations PASSED             [ 62%]
tests/test_pipeline.py::test_showcase_exhibits_integrity PASSED          [ 75%]
tests/test_pipeline.py::test_fact_supersession_audit_chain PASSED        [ 87%]
tests/test_pipeline.py::test_empty_key_handshake_validation PASSED       [100%]
============================== 8 passed in 0.50s ==============================
```

---

## ☁️ Cloud Deployment Blueprints

The repository includes production deployment configurations:

### Option A: Vercel Deployment
The repository includes `vercel.json` and `api/index.py` configured for `@vercel/python`:
1. Import repository into [Vercel](https://vercel.com).
2. Click **Deploy**.

### Option B: Docker / Railway / Fly.io
```bash
# Build and run container locally
docker build -t fact-detective-agency .
docker run -p 8000:8000 fact-detective-agency

# Or with Docker Compose
docker-compose up --build
```

### Option C: Render
Connect repository to [Render](https://render.com) using the included `render.yaml` blueprint.

---

## 📋 Rubric Compliance & Assignment Deliverables

| Requirement | Implementation & Traceability |
|---|---|
| **Atomic Fact Extraction** | Subject-Predicate-Object extraction with dynamic context qualifiers (fiscal year, reporting standards, units, currency). |
| **Evidence Provenance** | Character span grounding, page-level metadata, exact verbatim quotes, and fuzzy `SequenceMatcher` sliding window fallback. |
| **$O(K)$ Candidate Retrieval** | Subword n-gram vectorizer generating dense 256-dim embeddings with cosine similarity gating ($\ge 0.65$), eliminating $O(N^2)$ bottlenecks. |
| **Dual-Judge NLI Persona Debate** | Adversarial Skeptic vs. contextual Reconciler with automated Chief Magistrate tiebreak resolution. |
| **Lifecycle Supersession** | Formal retirement of obsolete facts with persistent `SUPERSEDED_BY` audit chains in SQLite. |
| **4+ Evaluation Exhibits** | 5 comprehensive exhibits covering Corroboration, Contradiction, Reconciliation (two-tier check), Supersession, and Honest Failure Analysis. |
| **Multi-Domain Generalization** | Zero hardcoded schemas; tested across Corporate Filings (Delhivery) and Macroeconomic Reports (India / RBI / IMF). |

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).

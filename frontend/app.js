// The Fact Detective Agency - Client Application Controller

const API_BASE = "";

// State
let appState = {
  activeTab: "showcase-tab",
  facts: [],
  documents: [],
  showcases: [],
  settings: null,
  activeFactId: null,
  selectedFile: null
};

// DOM Elements
const elements = {
  tabs: document.querySelectorAll(".nav-item"),
  tabViews: document.querySelectorAll(".tab-view"),
  showcaseContainer: document.getElementById("showcase-cards-container"),
  factsTableBody: document.getElementById("facts-table-body"),
  factSearchInput: document.getElementById("fact-search-input"),
  filterDoc: document.getElementById("filter-doc"),
  filterStatus: document.getElementById("filter-status"),
  filterMethod: document.getElementById("filter-method"),
  totalFactsBadge: document.getElementById("total-facts-badge"),
  sidebarIndexedFacts: document.getElementById("sidebar-indexed-facts"),
  sidebarTotalDocs: document.getElementById("sidebar-total-docs"),
  statusDot: document.getElementById("status-dot"),
  statusEngineName: document.getElementById("status-engine-name"),
  
  // Ingest
  uploadForm: document.getElementById("upload-form"),
  pdfFileInput: document.getElementById("pdf-file-input"),
  dropzoneArea: document.getElementById("dropzone-area"),
  selectedFileName: document.getElementById("selected-file-name"),
  uploadMaxPages: document.getElementById("upload-max-pages"),
  btnUploadSubmit: document.getElementById("btn-upload-submit"),
  ingestProgress: document.getElementById("ingest-progress"),
  progressText: document.getElementById("progress-text"),
  ingestResults: document.getElementById("ingest-results"),
  resultStatsBody: document.getElementById("result-stats-body"),
  ingestTelemetryBox: document.getElementById("ingest-telemetry-box"),
  ingestLogsBox: document.getElementById("ingest-logs-box"),
  ingestLogsContent: document.getElementById("ingest-logs-content"),
  
  // Quick ingest and topbar buttons
  btnTopbarUpload: document.getElementById("btn-topbar-upload"),
  btnQuickSampleA: document.getElementById("btn-quick-ingest-sample-a"),
  btnQuickSampleB: document.getElementById("btn-quick-ingest-sample-b"),
  btnResetShowcase: document.getElementById("btn-reset-showcase"),

  // Settings
  settingApiKey: document.getElementById("setting-api-key"),
  settingThreshold: document.getElementById("setting-threshold"),
  threshVal: document.getElementById("thresh-val"),
  btnSaveSettings: document.getElementById("btn-save-settings"),
  btnTestSettings: document.getElementById("btn-test-settings"),
  settingsStatusBanner: document.getElementById("settings-status-banner"),

  // Modal
  modal: document.getElementById("dossier-modal"),
  modalCloseBtn: document.getElementById("modal-close-btn"),
  modalFactTitle: document.getElementById("modal-fact-title"),
  modalVerdictBadge: document.getElementById("modal-verdict-badge"),
  modalFactStatement: document.getElementById("modal-fact-statement"),
  modalCredScore: document.getElementById("modal-cred-score"),
  modalCredFill: document.getElementById("modal-cred-fill"),
  modalFactStatus: document.getElementById("modal-fact-status"),
  modalFactMethod: document.getElementById("modal-fact-method"),
  modalSupersessionBox: document.getElementById("modal-supersession-box"),
  modalQualifiersList: document.getElementById("modal-qualifiers-list"),
  modalEvidenceDoc: document.getElementById("modal-evidence-doc"),
  modalEvidencePage: document.getElementById("modal-evidence-page"),
  modalEvidenceQuote: document.getElementById("modal-evidence-quote"),
  modalVerdictsContainer: document.getElementById("modal-verdicts-container")
};

// Initializer
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadSettings();
  loadShowcases();
  loadFactsAndDocs();
});

function initEventListeners() {
  // Navigation Tabs
  elements.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");
      switchTab(targetId);
    });
  });

  // Filters & Search
  elements.factSearchInput.addEventListener("input", debounce(filterAndRenderFacts, 200));
  elements.filterDoc.addEventListener("change", filterAndRenderFacts);
  elements.filterStatus.addEventListener("change", filterAndRenderFacts);
  if (elements.filterMethod) {
    elements.filterMethod.addEventListener("change", filterAndRenderFacts);
  }

  // Modal Close
  elements.modalCloseBtn.addEventListener("click", closeModal);
  elements.modal.addEventListener("click", (e) => {
    if (e.target === elements.modal) closeModal();
  });

  // Settings
  elements.settingThreshold.addEventListener("input", (e) => {
    elements.threshVal.textContent = e.target.value;
  });
  elements.btnSaveSettings.addEventListener("click", saveSettings);
  if (elements.btnTestSettings) {
    elements.btnTestSettings.addEventListener("click", testConnection);
  }

  // Topbar Actions
  if (elements.btnTopbarUpload) {
    elements.btnTopbarUpload.addEventListener("click", () => switchTab("ingest-tab"));
  }
  if (elements.btnQuickSampleA) {
    elements.btnQuickSampleA.addEventListener("click", () => runQuickIngest("delhivery", "Corporate Filings Corpus"));
  }
  if (elements.btnQuickSampleB) {
    elements.btnQuickSampleB.addEventListener("click", () => runQuickIngest("india-macroeconomy", "Macroeconomic Reports Corpus"));
  }
  elements.btnResetShowcase.addEventListener("click", resetShowcase);

  // Upload Portal (Single or Multiple PDFs)
  elements.dropzoneArea.addEventListener("click", () => elements.pdfFileInput.click());
  elements.pdfFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      appState.selectedFiles = Array.from(e.target.files);
      if (appState.selectedFiles.length === 1) {
        elements.selectedFileName.textContent = `Selected: ${appState.selectedFiles[0].name} (${(appState.selectedFiles[0].size / 1024 / 1024).toFixed(2)} MB)`;
      } else {
        elements.selectedFileName.textContent = `Selected ${appState.selectedFiles.length} PDF files ready for batch interrogation.`;
      }
    }
  });

  // Drag and drop
  elements.dropzoneArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    elements.dropzoneArea.style.borderColor = "var(--accent-cyan)";
  });
  elements.dropzoneArea.addEventListener("dragleave", () => {
    elements.dropzoneArea.style.borderColor = "var(--border-color)";
  });
  elements.dropzoneArea.addEventListener("drop", (e) => {
    e.preventDefault();
    elements.dropzoneArea.style.borderColor = "var(--border-color)";
    if (e.dataTransfer.files.length > 0) {
      const pdfs = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith(".pdf"));
      if (pdfs.length > 0) {
        appState.selectedFiles = pdfs;
        if (pdfs.length === 1) {
          elements.selectedFileName.textContent = `Selected: ${pdfs[0].name} (${(pdfs[0].size / 1024 / 1024).toFixed(2)} MB)`;
        } else {
          elements.selectedFileName.textContent = `Selected ${pdfs.length} PDF files ready for batch interrogation.`;
        }
      } else {
        alert("Please drop valid PDF file(s).");
      }
    }
  });

  elements.uploadForm.addEventListener("submit", handleUploadSubmit);
}

function switchTab(tabId) {
  elements.tabs.forEach(t => t.classList.toggle("active", t.getAttribute("data-tab") === tabId));
  elements.tabViews.forEach(v => v.classList.toggle("active", v.id === tabId));
  appState.activeTab = tabId;
  
  const pageTitle = document.getElementById("page-title");
  const pageDesc = document.getElementById("page-description");

  switch(tabId) {
    case "showcase-tab":
      if (pageTitle) pageTitle.textContent = "Benchmark Showcase Exhibits";
      if (pageDesc) pageDesc.textContent = "Demonstrating cross-document adjudication behaviors with exact evidence quotes and dual-judge reasoning.";
      loadShowcases();
      break;
    case "dossier-tab":
      if (pageTitle) pageTitle.textContent = "Knowledge Graph & Case Files";
      if (pageDesc) pageDesc.textContent = "Search, inspect, and audit extracted claims, dynamic qualifiers, evidence spans, and courtroom verdicts.";
      loadFactsAndDocs();
      break;
    case "ingest-tab":
      if (pageTitle) pageTitle.textContent = "Universal Document Intelligence";
      if (pageDesc) pageDesc.textContent = "Upload any PDF documents to run atomic fact extraction and real-time candidate adjudication.";
      break;
    case "settings-tab":
      if (pageTitle) pageTitle.textContent = "Frontier AI & Search Calibration";
      if (pageDesc) pageDesc.textContent = "Configure frontier API keys (Gemini, OpenAI, Claude) and tune retrieval similarity thresholds.";
      loadSettings();
      break;
  }
}

// ----------------- DATA FETCHING -----------------

async function loadShowcases() {
  try {
    const res = await fetch(`${API_BASE}/api/showcases`);
    const data = await res.json();
    appState.showcases = data;
    renderShowcases(data);
  } catch (err) {
    console.error("Failed to load showcase exhibits", err);
  }
}

async function loadFactsAndDocs() {
  try {
    const [factsRes, docsRes] = await Promise.all([
      fetch(`${API_BASE}/api/facts`),
      fetch(`${API_BASE}/api/documents`)
    ]);
    appState.facts = await factsRes.json();
    appState.documents = await docsRes.json();
    
    // Update badges
    elements.totalFactsBadge.textContent = appState.facts.length;
    elements.sidebarIndexedFacts.textContent = appState.facts.length;
    elements.sidebarTotalDocs.textContent = appState.documents.length;

    populateDocFilter();
    filterAndRenderFacts();
  } catch (err) {
    console.error("Failed to load facts and documents", err);
  }
}

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    const data = await res.json();
    appState.settings = data;

    elements.settingThreshold.value = data.similarity_threshold;
    elements.threshVal.textContent = data.similarity_threshold;
    
    updateEngineStatusBadge(data.llm_status);
  } catch (err) {
    console.error("Failed to load settings", err);
  }
}

function updateEngineStatusBadge(status) {
  const arbiterStatusEl = document.getElementById("sidebar-arbiter-status");
  const settingsStatusBadge = document.getElementById("settings-model-badge");
  const ingestIndicator = document.getElementById("ingest-engine-indicator");

  if (status && status.is_live_frontier_mode) {
    elements.statusDot.style.backgroundColor = "var(--accent-emerald)";
    elements.statusDot.style.boxShadow = "0 0 10px var(--accent-emerald)";
    elements.statusEngineName.textContent = status.engine_display_name;
    if (arbiterStatusEl) {
      arbiterStatusEl.textContent = "Live LLM";
      arbiterStatusEl.style.color = "var(--accent-emerald)";
    }
    if (settingsStatusBadge) {
      settingsStatusBadge.innerHTML = `🟢 <strong>Live Frontier Model:</strong> ${status.engine_display_name} (${status.masked_api_key})`;
      settingsStatusBadge.style.borderColor = "rgba(46, 160, 67, 0.4)";
      settingsStatusBadge.style.background = "rgba(46, 160, 67, 0.1)";
      settingsStatusBadge.style.color = "#3fb950";
    }
    if (ingestIndicator) {
      ingestIndicator.innerHTML = `🟢 <strong>Frontier LLM Active:</strong> Real-time multi-agent extraction & dual-judge generative NLI reasoning is online.`;
      ingestIndicator.style.borderColor = "rgba(46, 160, 67, 0.4)";
      ingestIndicator.style.background = "rgba(46, 160, 67, 0.1)";
      ingestIndicator.style.color = "#3fb950";
    }
    if (status.masked_api_key && elements.settingApiKey) {
      elements.settingApiKey.placeholder = `Active Key: ${status.masked_api_key} (Paste new key to replace)`;
    }
  } else {
    elements.statusDot.style.backgroundColor = "var(--text-muted)";
    elements.statusDot.style.boxShadow = "none";
    elements.statusEngineName.textContent = "Local Rule-Based NLI";
    if (arbiterStatusEl) {
      arbiterStatusEl.textContent = "Heuristic Fallback";
      arbiterStatusEl.style.color = "var(--text-secondary)";
    }
    if (settingsStatusBadge) {
      settingsStatusBadge.innerHTML = `⚪ <strong>Mode:</strong> Local Heuristic Engine (Enter API Key below to activate Live Frontier LLM)`;
      settingsStatusBadge.style.borderColor = "var(--border-color)";
      settingsStatusBadge.style.background = "var(--bg-card)";
      settingsStatusBadge.style.color = "var(--text-secondary)";
    }
    if (ingestIndicator) {
      ingestIndicator.innerHTML = `⚪ <strong>Engine Mode:</strong> Local Heuristic Pipeline (Rule-based extraction active. Connect an API Key in Settings for generative Frontier LLM reasoning).`;
      ingestIndicator.style.borderColor = "var(--border-color)";
      ingestIndicator.style.background = "var(--bg-card)";
      ingestIndicator.style.color = "var(--text-secondary)";
    }
    if (elements.settingApiKey) {
      elements.settingApiKey.placeholder = "Paste your API key here (e.g. AIzaSy... or sk-...)";
    }
  }
}

function detectProvider(key) {
  const k = (key || "").trim();
  if (k.startsWith("AIzaSy")) return "gemini";
  if (k.startsWith("sk-ant-")) return "anthropic";
  if (k.startsWith("sk-")) return "openai";
  return "gemini";
}

async function testConnection() {
  const apiKey = elements.settingApiKey.value.trim();
  const banner = elements.settingsStatusBanner;

  if (!apiKey && (!appState.settings || !appState.settings.llm_status.has_api_key)) {
    banner.style.display = "block";
    banner.style.background = "rgba(248, 81, 73, 0.15)";
    banner.style.border = "1px solid rgba(248, 81, 73, 0.5)";
    banner.style.color = "#f85149";
    banner.innerHTML = `<strong>❌ No API Key Entered:</strong> Please paste an API key in the field above before testing handshake.`;
    return;
  }

  const provider = detectProvider(apiKey);
  banner.style.display = "block";
  banner.style.background = "var(--bg-card)";
  banner.style.border = "1px solid var(--border-color)";
  banner.style.color = "var(--text-primary)";
  banner.innerHTML = `<span>⏳ Testing live handshake with <strong>${provider.toUpperCase()}</strong> endpoint...</span>`;

  try {
    const res = await fetch(`${API_BASE}/api/settings/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key: apiKey })
    });
    const data = await res.json();

    if (data.ok) {
      banner.style.background = "rgba(46, 160, 67, 0.15)";
      banner.style.border = "1px solid rgba(46, 160, 67, 0.5)";
      banner.style.color = "#3fb950";
      banner.innerHTML = `<strong>✅ Handshake Succeeded:</strong> ${data.message}`;
    } else {
      banner.style.background = "rgba(248, 81, 73, 0.15)";
      banner.style.border = "1px solid rgba(248, 81, 73, 0.5)";
      banner.style.color = "#f85149";
      banner.innerHTML = `<strong>❌ Handshake Failed:</strong> ${data.error}`;
    }
  } catch (err) {
    banner.style.background = "rgba(248, 81, 73, 0.15)";
    banner.style.border = "1px solid rgba(248, 81, 73, 0.5)";
    banner.style.color = "#f85149";
    banner.innerHTML = `<strong>❌ Connection Error:</strong> ${err.message}`;
  }
}

async function saveSettings() {
  const apiKey = elements.settingApiKey.value.trim();
  const provider = detectProvider(apiKey);
  const threshold = parseFloat(elements.settingThreshold.value);
  const banner = elements.settingsStatusBanner;

  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: provider,
        api_key: apiKey,
        similarity_threshold: threshold
      })
    });
    const result = await res.json();
    
    if (res.ok) {
      const status = result.settings.llm_status;
      appState.settings = result.settings;
      updateEngineStatusBadge(status);

      banner.style.display = "block";
      if (status.is_live_frontier_mode) {
        banner.style.background = "rgba(46, 160, 67, 0.15)";
        banner.style.border = "1px solid rgba(46, 160, 67, 0.5)";
        banner.style.color = "#3fb950";
        banner.innerHTML = `<strong>🚀 Frontier Engine Active:</strong> Connected to <strong>${status.engine_display_name}</strong> (${status.masked_api_key}). All extraction & adjudication is now powered by frontier LLM inference!`;
        elements.settingApiKey.value = "";
      } else {
        banner.style.background = "rgba(56, 139, 253, 0.15)";
        banner.style.border = "1px solid rgba(56, 139, 253, 0.4)";
        banner.style.color = "var(--accent-cyan)";
        banner.innerHTML = `<strong>ℹ️ Configuration Saved:</strong> Operating in Local Heuristic Engine mode. Vector threshold set to ${threshold}.`;
      }
    }
  } catch (err) {
    banner.style.display = "block";
    banner.style.background = "rgba(248, 81, 73, 0.15)";
    banner.style.border = "1px solid rgba(248, 81, 73, 0.5)";
    banner.style.color = "#f85149";
    banner.innerHTML = `<strong>❌ Error Saving:</strong> ${err.message}`;
  }
}

// ----------------- RENDERING -----------------

function renderShowcases(showcases) {
  elements.showcaseContainer.innerHTML = "";

  showcases.forEach(sc => {
    const card = document.createElement("div");
    card.className = "showcase-card";

    const badgeClass = getBadgeClass(sc.verdict_type);

    let failureHtml = "";
    if (sc.failure_mode_analysis) {
      const f = sc.failure_mode_analysis;
      failureHtml = `
        <div style="background: rgba(219, 109, 40, 0.12); border: 1px solid rgba(219, 109, 40, 0.4); border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
          <strong style="color: #ffa657; font-size: 0.85rem; display: block; margin-bottom: 0.25rem;">⚠️ Honest Failure & Edge-Case Audit: ${f.edge_case_type}</strong>
          <p style="font-size: 0.8rem; color: #f0f6fc; margin-bottom: 0.4rem;">${f.description}</p>
          <div style="font-size: 0.78rem; color: #8b949e; background: rgba(0,0,0,0.3); padding: 0.6rem; border-radius: 4px; white-space: pre-line;">
            <strong>How to Improve:</strong>\n${f.how_to_improve}
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="showcase-card-header">
        <div>
          <span class="showcase-dataset-tag">${sc.dataset}</span>
          <h3 class="showcase-card-title" style="margin-top: 0.35rem;">${sc.title}</h3>
        </div>
        <span class="verdict-badge ${badgeClass}">${sc.verdict_type}</span>
      </div>

      <p class="showcase-summary">${sc.summary}</p>

      <div class="comparison-container">
        <div class="fact-box">
          <span class="fact-box-label">Fact A</span>
          <div class="fact-box-text">${sc.fact_1.subject} &rarr; ${sc.fact_1.predicate} &rarr; <strong>${sc.fact_1.object}</strong></div>
          <div class="fact-box-doc">📄 ${sc.fact_1.evidence.doc_name} (Page ${sc.fact_1.evidence.page_number})</div>
          <blockquote style="font-size:0.75rem; color:#8b949e; font-style:italic; border-left:2px solid var(--accent-gold); padding-left:0.4rem; margin-top:0.3rem;">"${sc.fact_1.evidence.exact_text_span}"</blockquote>
        </div>

        <div class="fact-box">
          <span class="fact-box-label">Fact B</span>
          <div class="fact-box-text">${sc.fact_2.subject} &rarr; ${sc.fact_2.predicate} &rarr; <strong>${sc.fact_2.object}</strong></div>
          <div class="fact-box-doc">📄 ${sc.fact_2.evidence.doc_name} (Page ${sc.fact_2.evidence.page_number})</div>
          <blockquote style="font-size:0.75rem; color:#8b949e; font-style:italic; border-left:2px solid var(--accent-gold); padding-left:0.4rem; margin-top:0.3rem;">"${sc.fact_2.evidence.exact_text_span}"</blockquote>
        </div>
      </div>

      <div class="judges-grid">
        <div class="judge-box judge-skeptic">
          <div class="judge-header"><span style="color:var(--accent-crimson);">🗡️ Skeptic Judge</span></div>
          <p class="judge-text">${sc.courtroom.skeptic_reasoning}</p>
        </div>
        <div class="judge-box judge-reconciler">
          <div class="judge-header"><span style="color:var(--accent-cyan);">⚖️ Reconciler Judge</span></div>
          <p class="judge-text">${sc.courtroom.reconciler_reasoning}</p>
        </div>
      </div>

      <div class="adjudication-result-box">
        <strong>Courtroom Final Reasoning:</strong>
        <p style="margin-top: 0.25rem; font-size: 0.84rem; color: #f0f6fc;">${sc.courtroom.final_reasoning}</p>
      </div>

      ${failureHtml}

      <div style="display:flex; justify-content:flex-end; margin-top:0.5rem;">
        <button class="btn btn-outline" onclick="openFactModal('${sc.fact_1.id}')">🔍 Open Fact A Dossier</button>
      </div>
    `;

    elements.showcaseContainer.appendChild(card);
  });
}

function populateDocFilter() {
  elements.filterDoc.innerHTML = `<option value="">All Documents (${appState.documents.length})</option>`;
  appState.documents.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = `${d.filename} (${d.fact_count} facts)`;
    elements.filterDoc.appendChild(opt);
  });
}

function filterAndRenderFacts() {
  const query = elements.factSearchInput.value.toLowerCase().trim();
  const selectedDoc = elements.filterDoc.value;
  const selectedStatus = elements.filterStatus.value;
  const selectedMethod = elements.filterMethod ? elements.filterMethod.value : "";

  const filtered = appState.facts.filter(f => {
    if (selectedDoc && f.doc_id !== selectedDoc) return false;
    if (selectedStatus && f.status !== selectedStatus) return false;
    if (selectedMethod && f.extraction_method !== selectedMethod) return false;
    if (query) {
      const matchSubj = f.subject.toLowerCase().includes(query);
      const matchPred = f.predicate.toLowerCase().includes(query);
      const matchObj = f.object.toLowerCase().includes(query);
      const matchSpan = f.evidence.exact_text_span.toLowerCase().includes(query);
      return matchSubj || matchPred || matchObj || matchSpan;
    }
    return true;
  });

  elements.factsTableBody.innerHTML = "";
  if (filtered.length === 0) {
    elements.factsTableBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--text-muted);">No facts match current filters.</td></tr>`;
    return;
  }

  filtered.forEach(fact => {
    const tr = document.createElement("tr");

    const qualChips = Object.entries(fact.qualifiers || {})
      .map(([k, v]) => `<span class="qualifier-chip">${k}: ${v}</span>`)
      .join("");

    const credPercent = Math.round(fact.credibility * 100);
    const statusBadge = fact.status === "SUPERSEDED" ? "badge-superseded" : "badge-corroborated";
    const methodBadge = fact.extraction_method === "frontier_llm" 
      ? `<span style="font-size:0.72rem; padding:0.2rem 0.5rem; border-radius:4px; background:rgba(56, 139, 253, 0.15); color:var(--accent-cyan); border:1px solid rgba(56, 139, 253, 0.4); white-space:nowrap;">✨ Frontier LLM</span>`
      : `<span style="font-size:0.72rem; padding:0.2rem 0.5rem; border-radius:4px; background:rgba(139, 148, 158, 0.15); color:var(--text-secondary); border:1px solid var(--border-color); white-space:nowrap;">⚙️ Heuristic</span>`;

    tr.innerHTML = `
      <td class="statement-cell">
        <strong>${escapeHtml(fact.subject)}</strong><br/>
        <span style="color:var(--text-secondary); font-size:0.75rem;">&rarr; ${escapeHtml(fact.predicate)}</span>
      </td>
      <td><strong>${escapeHtml(fact.object)}</strong></td>
      <td style="max-width: 200px;">${qualChips || '<span style="color:var(--text-muted); font-size:0.75rem;">None</span>'}</td>
      <td>
        <div class="cred-meter-wrap">
          <div class="cred-bar"><div class="cred-fill" style="width:${credPercent}%;"></div></div>
          <span style="font-size:0.78rem; font-weight:700;">${fact.credibility.toFixed(2)}</span>
        </div>
      </td>
      <td>${methodBadge}</td>
      <td><span class="verdict-badge ${statusBadge}">${fact.status}</span></td>
      <td style="font-size:0.78rem; color:var(--text-secondary);">
        📄 ${escapeHtml(fact.evidence.doc_name)} <span class="page-tag">P.${fact.evidence.page_number}</span>
      </td>
      <td>
        <button class="btn btn-outline" style="padding:0.3rem 0.6rem; font-size:0.78rem;" onclick="openFactModal('${fact.id}')">Inspect</button>
      </td>
    `;
    elements.factsTableBody.appendChild(tr);
  });
}

// ----------------- DOSSIER MODAL -----------------

window.openFactModal = async function(factId) {
  try {
    const res = await fetch(`${API_BASE}/api/facts/${factId}`);
    if (!res.ok) throw new Error("Fact not found");
    const dossier = await res.json();
    const fact = dossier.fact;

    appState.activeFactId = fact.id;

    elements.modalFactTitle.textContent = `Fact Dossier #${fact.id}`;
    elements.modalFactStatement.innerHTML = `<strong>${escapeHtml(fact.subject)}</strong> &rarr; <span style="color:var(--accent-cyan);">${escapeHtml(fact.predicate)}</span> &rarr; <span style="color:var(--accent-gold); font-weight:700;">${escapeHtml(fact.object)}</span>`;
    
    elements.modalCredScore.textContent = fact.credibility.toFixed(2);
    elements.modalCredFill.style.width = `${Math.round(fact.credibility * 100)}%`;
    elements.modalFactStatus.textContent = fact.status;
    elements.modalFactStatus.className = `status-badge ${fact.status === 'SUPERSEDED' ? 'badge-superseded' : 'badge-corroborated'}`;

    // Extraction Provenance
    if (elements.modalFactMethod) {
      if (fact.extraction_method === "frontier_llm") {
        elements.modalFactMethod.textContent = "✨ Frontier LLM Extracted";
        elements.modalFactMethod.style.background = "rgba(46, 160, 67, 0.15)";
        elements.modalFactMethod.style.color = "#3fb950";
        elements.modalFactMethod.style.borderColor = "rgba(46, 160, 67, 0.4)";
      } else {
        elements.modalFactMethod.textContent = "⚙️ Heuristic Rule-Based";
        elements.modalFactMethod.style.background = "rgba(139, 148, 158, 0.15)";
        elements.modalFactMethod.style.color = "var(--text-secondary)";
        elements.modalFactMethod.style.borderColor = "var(--border-color)";
      }
    }

    // Supersession Audit Chain Box
    if (elements.modalSupersessionBox) {
      if (fact.status === "SUPERSEDED" || fact.superseded_by) {
        elements.modalSupersessionBox.style.display = "block";
        elements.modalSupersessionBox.innerHTML = `
          <strong style="color:#ffa657;">🔄 Supersession Audit Chain:</strong>
          <p style="margin-top:0.25rem; color:#f0f6fc;">This historical claim was formally superseded by newer filing evidence <strong>Fact #${fact.superseded_by || 'Newer Claim'}</strong>${fact.superseded_at ? ` on ${fact.superseded_at.split('T')[0]}` : ''}.</p>
        `;
      } else if (fact.supersedes_fact_id) {
        elements.modalSupersessionBox.style.display = "block";
        elements.modalSupersessionBox.innerHTML = `
          <strong style="color:var(--accent-cyan);">🔄 Supersession Audit Chain:</strong>
          <p style="margin-top:0.25rem; color:#f0f6fc;">This updated claim chronologically supersedes historical claim <strong>Fact #${fact.supersedes_fact_id}</strong>.</p>
        `;
      } else {
        elements.modalSupersessionBox.style.display = "none";
      }
    }

    // Qualifiers
    elements.modalQualifiersList.innerHTML = "";
    const qualEntries = Object.entries(fact.qualifiers || {});
    if (qualEntries.length === 0) {
      elements.modalQualifiersList.innerHTML = `<span style="color:var(--text-muted); font-size:0.85rem;">No dynamic qualifiers attached.</span>`;
    } else {
      qualEntries.forEach(([k, v]) => {
        const tag = document.createElement("span");
        tag.className = "qualifier-chip";
        tag.style.fontSize = "0.82rem";
        tag.style.padding = "0.25rem 0.6rem";
        tag.textContent = `${k}: ${v}`;
        elements.modalQualifiersList.appendChild(tag);
      });
    }

    // Evidence
    elements.modalEvidenceDoc.textContent = dossier.document_name || fact.evidence.doc_name;
    elements.modalEvidencePage.textContent = `Page ${fact.evidence.page_number}`;
    elements.modalEvidenceQuote.textContent = `"${fact.evidence.exact_text_span}"`;

    // Verdicts & Courtroom
    elements.modalVerdictsContainer.innerHTML = "";
    if (dossier.verdicts.length === 0) {
      elements.modalVerdictBadge.textContent = "UNADJUDICATED";
      elements.modalVerdictBadge.className = "modal-badge";
      elements.modalVerdictsContainer.innerHTML = `<p style="color:var(--text-muted); font-size:0.88rem;">No semantic candidate facts have been cross-examined against this fact yet.</p>`;
    } else {
      const primaryVerdict = dossier.verdicts[0];
      elements.modalVerdictBadge.textContent = primaryVerdict.verdict_type;
      elements.modalVerdictBadge.className = `modal-badge ${getBadgeClass(primaryVerdict.verdict_type)}`;

      dossier.verdicts.forEach(v => {
        const vCard = document.createElement("div");
        vCard.style.background = "var(--bg-card)";
        vCard.style.border = "1px solid var(--border-color)";
        vCard.style.borderRadius = "8px";
        vCard.style.padding = "1rem";
        vCard.style.marginBottom = "1rem";

        let tiebreakBtn = "";
        if (v.verdict_type === "HUNG_JURY") {
          tiebreakBtn = `
            <div class="tiebreak-banner">
              <span style="font-size:0.82rem; color:#ffa657;">⚠️ Judges in Deadlock: Skeptic and Reconciler disagree.</span>
              <button class="btn btn-primary" style="padding:0.35rem 0.75rem; font-size:0.78rem;" onclick="runTiebreak('${v.id}')">⚡ Chief Magistrate Tiebreak</button>
            </div>
          `;
        }

        vCard.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
            <span class="verdict-badge ${getBadgeClass(v.verdict_type)}">${v.verdict_type}</span>
            <span style="font-size:0.75rem; color:var(--text-muted);">Cosine Sim: ${(v.similarity_score * 100).toFixed(1)}%</span>
          </div>

          <div class="judges-grid">
            <div class="judge-box judge-skeptic">
              <div class="judge-header"><span style="color:var(--accent-crimson);">🗡️ Skeptic Judge Opinion</span></div>
              <p class="judge-text">${escapeHtml(v.skeptic_reasoning)}</p>
            </div>
            <div class="judge-box judge-reconciler">
              <div class="judge-header"><span style="color:var(--accent-cyan);">⚖️ Reconciler Judge Opinion</span></div>
              <p class="judge-text">${escapeHtml(v.reconciler_reasoning)}</p>
            </div>
          </div>

          <div style="background:rgba(0,0,0,0.3); padding:0.75rem; border-radius:6px; margin-top:0.75rem;">
            <strong style="font-size:0.82rem; color:var(--text-primary);">Courtroom Ruling:</strong>
            <p style="font-size:0.84rem; color:var(--text-secondary); margin-top:0.2rem;">${escapeHtml(v.final_reasoning)}</p>
            ${v.reconciliation_reason ? `<div style="font-size:0.8rem; color:var(--accent-purple); margin-top:0.3rem;"><strong>Reconciliation Note:</strong> ${escapeHtml(v.reconciliation_reason)}</div>` : ''}
          </div>

          ${tiebreakBtn}
        `;
        elements.modalVerdictsContainer.appendChild(vCard);
      });
    }

    elements.modal.style.display = "flex";
  } catch (err) {
    alert("Error loading fact dossier: " + err.message);
  }
};

window.runTiebreak = async function(verdictId) {
  try {
    const res = await fetch(`${API_BASE}/api/verdicts/${verdictId}/tiebreak`, { method: "POST" });
    const data = await res.json();
    alert(`Chief Magistrate Resolution: ${data.verdict}\n\n${data.arbitration.final_reasoning}`);
    if (appState.activeFactId) {
      openFactModal(appState.activeFactId);
    }
  } catch (err) {
    alert("Tiebreak execution error: " + err.message);
  }
};

function closeModal() {
  elements.modal.style.display = "none";
  appState.activeFactId = null;
}

// ----------------- INGESTION -----------------

async function handleUploadSubmit(e) {
  e.preventDefault();
  const files = appState.selectedFiles || (appState.selectedFile ? [appState.selectedFile] : []);
  if (files.length === 0) {
    alert("Please select one or more PDF files first.");
    return;
  }

  elements.ingestProgress.style.display = "block";
  elements.ingestResults.style.display = "none";
  const maxPages = elements.uploadMaxPages.value || 20;

  let totalExtracted = 0;
  let totalAdjudications = 0;
  let totalProcessedPages = 0;
  let totalLatency = 0;
  let totalLlmCalls = 0;
  let allLogs = [];
  let lastMode = "heuristic_fallback";

  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      elements.progressText.textContent = `Interrogating Document [${i + 1}/${files.length}]: ${file.name}...`;

      const formData = new FormData();
      formData.append("file", file);
      formData.append("max_pages", maxPages);

      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      totalExtracted += (data.facts_extracted || 0);
      totalAdjudications += (data.adjudications_performed || 0);
      totalProcessedPages += (data.total_pages || 0);
      totalLatency += (data.latency_seconds || 0);
      totalLlmCalls += (data.llm_calls_made || 0);
      lastMode = data.extraction_mode || lastMode;
      if (data.execution_log && Array.isArray(data.execution_log)) {
        allLogs = allLogs.concat(data.execution_log);
      }
    }

    elements.ingestProgress.style.display = "none";
    elements.ingestResults.style.display = "block";

    renderIngestStats({
      total_pages: totalProcessedPages,
      facts_extracted: totalExtracted,
      adjudications_performed: totalAdjudications,
      latency_seconds: totalLatency.toFixed(2),
      llm_calls_made: totalLlmCalls,
      extraction_mode: lastMode,
      execution_log: allLogs
    });

    loadFactsAndDocs();
  } catch (err) {
    elements.ingestProgress.style.display = "none";
    alert("Upload/Ingestion failed: " + err.message);
  }
}

async function runQuickIngest(datasetName, displayName) {
  const label = displayName || datasetName;
  if (!confirm(`Ingest ${label}? The Detective will extract facts across all documents and run real-time Courtroom candidate adjudication.`)) {
    return;
  }

  switchTab("ingest-tab");
  elements.ingestProgress.style.display = "block";
  elements.ingestResults.style.display = "none";
  elements.progressText.textContent = `Batch processing ${label}...`;

  const formData = new FormData();
  formData.append("dataset_name", datasetName);
  formData.append("max_pages", "20");

  try {
    const res = await fetch(`${API_BASE}/api/starter/ingest`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    elements.ingestProgress.style.display = "none";
    elements.ingestResults.style.display = "block";

    let totalExtracted = 0;
    let totalAdjudications = 0;
    let totalPages = 0;
    let totalLatency = 0;
    let totalLlmCalls = 0;
    let allLogs = [];
    let lastMode = "heuristic_fallback";

    data.documents.forEach(d => {
      totalExtracted += (d.facts_extracted || 0);
      totalAdjudications += (d.adjudications_performed || 0);
      totalPages += (d.total_pages || 0);
      totalLatency += (d.latency_seconds || 0);
      totalLlmCalls += (d.llm_calls_made || 0);
      lastMode = d.extraction_mode || lastMode;
      if (d.execution_log && Array.isArray(d.execution_log)) {
        allLogs = allLogs.concat(d.execution_log);
      }
    });

    renderIngestStats({
      total_pages: totalPages,
      facts_extracted: totalExtracted,
      adjudications_performed: totalAdjudications,
      latency_seconds: totalLatency.toFixed(2),
      llm_calls_made: totalLlmCalls,
      extraction_mode: lastMode,
      execution_log: allLogs
    });

    loadFactsAndDocs();
  } catch (err) {
    elements.ingestProgress.style.display = "none";
    alert("Batch ingest failed: " + err.message);
  }
}

async function resetShowcase() {
  try {
    await fetch(`${API_BASE}/api/showcases/reset`, { method: "POST" });
    alert("Showcase benchmark exhibits refreshed!");
    loadShowcases();
    loadFactsAndDocs();
  } catch (err) {
    alert("Reset failed: " + err.message);
  }
}

function renderIngestStats(data) {
  elements.resultStatsBody.innerHTML = `
    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:0.75rem; margin-top:0.75rem;">
      <div style="background:var(--bg-card); padding:0.75rem; border-radius:6px;">
        <span style="font-size:0.72rem; color:var(--text-muted);">Pages Processed</span>
        <h4 style="color:var(--text-primary);">${data.total_pages}</h4>
      </div>
      <div style="background:var(--bg-card); padding:0.75rem; border-radius:6px;">
        <span style="font-size:0.72rem; color:var(--text-muted);">Atomic Facts</span>
        <h4 style="color:var(--accent-cyan);">${data.facts_extracted}</h4>
      </div>
      <div style="background:var(--bg-card); padding:0.75rem; border-radius:6px;">
        <span style="font-size:0.72rem; color:var(--text-muted);">Adjudications</span>
        <h4 style="color:var(--accent-gold);">${data.adjudications_performed}</h4>
      </div>
      <div style="background:var(--bg-card); padding:0.75rem; border-radius:6px;">
        <span style="font-size:0.72rem; color:var(--text-muted);">Execution Latency</span>
        <h4 style="color:#3fb950;">${data.latency_seconds || '0.00'}s</h4>
      </div>
    </div>
  `;

  if (elements.ingestTelemetryBox) {
    const isLLM = data.extraction_mode === "frontier_llm";
    elements.ingestTelemetryBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.25); padding:0.6rem 0.85rem; border-radius:6px; font-size:0.8rem; border:1px solid var(--border-color);">
        <span>⚙️ <strong>Inference Engine:</strong> ${isLLM ? '<span style="color:#3fb950;">✨ Frontier LLM</span>' : '<span style="color:var(--text-secondary);">Local Rule-Based NLI</span>'}</span>
        <span>⚡ <strong>LLM API Calls Made:</strong> <strong style="color:var(--accent-cyan);">${data.llm_calls_made || 0}</strong></span>
      </div>
    `;
  }

  if (elements.ingestLogsBox && elements.ingestLogsContent) {
    if (data.execution_log && data.execution_log.length > 0) {
      elements.ingestLogsBox.style.display = "block";
      elements.ingestLogsContent.textContent = data.execution_log.join("\n");
      elements.ingestLogsContent.scrollTop = elements.ingestLogsContent.scrollHeight;
    } else {
      elements.ingestLogsBox.style.display = "none";
    }
  }
}

// ----------------- UTILITIES -----------------

function getBadgeClass(verdictType) {
  switch (verdictType) {
    case "CORROBORATED": return "badge-corroborated";
    case "CONTRADICTED": return "badge-contradicted";
    case "RECONCILED": return "badge-reconciled";
    case "HUNG_JURY": return "badge-hung";
    case "SUPERSEDED_BY": return "badge-superseded";
    default: return "";
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

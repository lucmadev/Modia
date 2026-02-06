let explain = false;
let raw = false;

document.getElementById("explainBtn").onclick = () => {
  explain = !explain;
  toggle("explainBtn", explain);
};

document.getElementById("rawBtn").onclick = () => {
  raw = !raw;
  toggle("rawBtn", raw);
};

function toggle(id, state) {
  document.getElementById(id).classList.toggle("bg-indigo-600", state);
}

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const statusText = document.getElementById("statusText");
const clearBtn = document.getElementById("clearBtn");
const menuBtn = document.getElementById("menuBtn");
const menuPanel = document.getElementById("menuPanel");
const providerSelect = document.getElementById("providerSelect");
const modelSelect = document.getElementById("modelSelect");
const applyModelBtn = document.getElementById("applyModelBtn");
const currentModelText = document.getElementById("currentModelText");
const apiKeyInput = document.getElementById("apiKeyInput");
const baseUrlInput = document.getElementById("baseUrlInput");
const saveApiBtn = document.getElementById("saveApiBtn");
const repoUrlInput = document.getElementById("repoUrlInput");
const addRepoBtn = document.getElementById("addRepoBtn");
const syncReposBtn = document.getElementById("syncReposBtn");
const repoList = document.getElementById("repoList");
const refreshStatsBtn = document.getElementById("refreshStatsBtn");
const rebuildDbBtn = document.getElementById("rebuildDbBtn");
const dbStatsText = document.getElementById("dbStatsText");
const opsLog = document.getElementById("opsLog");
const opsProgress = document.getElementById("opsProgress");
const chatFooter = document.getElementById("chatFooter");

const initialChatHtml = chatEl.innerHTML;

let selectedProvider = localStorage.getItem("modia_provider") || "";
let selectedModel = localStorage.getItem("modia_model") || "";

sendBtn.onclick = send;
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    send();
  }
});

if (clearBtn) {
  clearBtn.onclick = () => {
    chatEl.innerHTML = initialChatHtml;
  };
}

// Estado del backend
checkHealth();

// Menú
if (menuBtn && menuPanel) {
  menuBtn.onclick = () => {
    menuPanel.classList.toggle("hidden");
    if (chatFooter) {
      chatFooter.classList.toggle("hidden", !menuPanel.classList.contains("hidden"));
    }
    if (!menuPanel.classList.contains("hidden")) {
      loadProviders();
      refreshRepos();
      refreshDbStats();
    }
  };
}

if (applyModelBtn) {
  applyModelBtn.onclick = () => {
    selectedProvider = String(providerSelect?.value || "");
    selectedModel = String(modelSelect?.value || "");
    localStorage.setItem("modia_provider", selectedProvider);
    localStorage.setItem("modia_model", selectedModel);
    renderCurrentModel();
    log(`Aplicado: provider=${selectedProvider || "(default)"} model=${selectedModel || "(default)"}`);
  };
}

if (saveApiBtn) {
  saveApiBtn.onclick = async () => {
    const provider = String(providerSelect?.value || "").trim();
    const apiKey = String(apiKeyInput?.value || "").trim();
    const baseUrl = String(baseUrlInput?.value || "").trim();

    if (!provider) {
      log("Elegí un provider primero.");
      return;
    }
    if (!apiKey) {
      log("Ingresá una API key.");
      return;
    }

    await runOp("Guardando API key...", async () => {
      const res = await fetch("/api/llm/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          api_key: apiKey,
          base_url: baseUrl || null
        })
      });
      const data = await safeJson(res);
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);

      // set default provider para que el backend lo use por defecto
      await fetch(`/api/llm/set-default?provider=${encodeURIComponent(provider)}`, { method: "POST" });

      apiKeyInput.value = "";
      log(data?.message || "API key guardada.");
      await loadProviders(true);
    });
  };
}

if (addRepoBtn) {
  addRepoBtn.onclick = async () => {
    const url = String(repoUrlInput?.value || "").trim();
    if (!url) return;
    await runOp("Añadiendo repo...", async () => {
      const res = await fetch("/api/repos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      const data = await safeJson(res);
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      repoUrlInput.value = "";
      await refreshRepos();
      log("Repo añadido.");
    });
  };
}

if (syncReposBtn) {
  syncReposBtn.onclick = async () => {
    await runOp("Sync repos (git clone/pull)...", async () => {
      const res = await fetch("/api/repos/sync", { method: "POST" });
      const data = await safeJson(res);
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      renderSteps(data?.steps);
      logBlock("Sync repos", data?.logs || "Sync terminado.");
    });
  };
}

if (refreshStatsBtn) {
  refreshStatsBtn.onclick = refreshDbStats;
}

if (rebuildDbBtn) {
  rebuildDbBtn.onclick = async () => {
    await runOp("Actualizando base (extractChunks → buildDB)...", async () => {
      const res = await fetch("/api/db/rebuild", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sync_repos: true })
      });
      const data = await safeJson(res);
      if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
      renderSteps(data?.steps);
      logBlock("Rebuild DB", data?.logs || "Rebuild terminado.");
      await refreshDbStats();
    });
  };
}

async function send() {
  const text = inputEl.value.trim();
  if (!text) return;

  addMessage("user", text);
  inputEl.value = "";
  inputEl.focus();

  const loadingEl = addMessage("ai", "Pensando...");
  setStatus("● Pensando…", true);
  setSending(true);

  try {
    // Si Raw está activo, mostramos fuentes (RAG) en paralelo
    let ragText = null;
    if (raw) {
      ragText = await fetchRagSources(text);
    }

    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        top_k: 5,
        explain_mode: explain,
        provider: selectedProvider || null,
        model: selectedModel || null
      })
    });

    let data = null;
    try {
      data = await res.json();
    } catch {
      // ignore
    }

    if (!res.ok) {
      const detail = data?.detail ? String(data.detail) : `HTTP ${res.status}`;
      loadingEl.innerText = `Error: ${detail}`;
      setStatus("● Error", false);
      return;
    }

    if (ragText) {
      const ragEl = addMessage("ai", ragText);
      ragEl.classList.add("code-block");
    }

    loadingEl.innerText = String(data?.answer ?? "");
    setStatus("● Listo", true);
  } catch (e) {
    loadingEl.innerText = `Error: ${String(e?.message ?? e)}`;
    setStatus("● Error", false);
  } finally {
    setSending(false);
  }
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = role === "user" ? "message-user" : "message-ai";
  div.innerText = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function setSending(sending) {
  sendBtn.disabled = sending;
  sendBtn.innerText = sending ? "Enviando..." : "Enviar";
}

function setStatus(text, ok) {
  if (!statusText) return;
  statusText.innerText = text;
  statusText.classList.toggle("text-green-400", !!ok);
  statusText.classList.toggle("text-zinc-400", !ok);
}

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) {
      setStatus("● Offline", false);
      return;
    }
    const data = await res.json();
    if (data?.status === "ok") {
      setStatus("● Listo", true);
    } else {
      setStatus("● Offline", false);
    }
  } catch {
    setStatus("● Offline", false);
  }
}

async function fetchRagSources(query) {
  try {
    const url = `/api/db/search?query=${encodeURIComponent(query)}&k=5`;
    const res = await fetch(url);
    if (!res.ok) return "Fuentes (RAG): no disponibles.";
    const data = await res.json();
    const results = Array.isArray(data?.results) ? data.results : [];
    if (!results.length) return "Fuentes (RAG): sin resultados.";

    const lines = ["Fuentes (RAG) — top 5:"];
    for (let i = 0; i < results.length; i++) {
      const content = String(results[i]?.content ?? "").trim();
      const short = content.length > 300 ? content.slice(0, 300) + "…" : content;
      lines.push(`\n[${i + 1}] ${short}`);
    }
    return lines.join("\n");
  } catch {
    return "Fuentes (RAG): error al consultar.";
  }
}

function log(text) {
  if (!opsLog) return;
  opsLog.innerText = String(text || "").trim() || "Listo.";
}

function logBlock(title, body) {
  if (!opsLog) return;
  const ts = new Date().toLocaleString();
  const chunk = `\n\n[${ts}] ${title}\n${String(body || "").trim()}`.trimEnd();
  const next = (opsLog.innerText || "").trimEnd() + chunk;
  // Evitar que crezca infinito
  opsLog.innerText = next.slice(-20000);
}

async function safeJson(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

async function runOp(title, fn) {
  log(title);
  renderSteps([]);
  setStatus("● Operación…", true);
  try {
    await fn();
    setStatus("● Listo", true);
  } catch (e) {
    log(`Error: ${String(e?.message ?? e)}`);
    setStatus("● Error", false);
  }
}

function renderSteps(steps) {
  if (!opsProgress) return;
  if (!Array.isArray(steps) || !steps.length) {
    opsProgress.innerText = "Sin operaciones en curso.";
    return;
  }

  const lines = [];
  for (const s of steps) {
    const name = String(s?.name ?? "Paso");
    const ok = !!s?.ok;
    const dur = typeof s?.duration_ms === "number" ? `${s.duration_ms}ms` : "";
    lines.push(`${ok ? "✓" : "✗"} ${name} ${dur}`.trim());
  }
  opsProgress.innerText = lines.join("\n");
}

function renderCurrentModel() {
  if (!currentModelText) return;
  const p = selectedProvider ? selectedProvider : "(default)";
  const m = selectedModel ? selectedModel : "(default)";
  currentModelText.innerText = `Actual: provider=${p} · model=${m}`;
}

async function loadProviders(keepSelection = false) {
  if (!providerSelect || !modelSelect) return;

  const res = await fetch("/api/llm/providers");
  const data = await safeJson(res);
  if (!res.ok) {
    log(data?.detail || `No se pudo cargar providers (HTTP ${res.status})`);
    return;
  }

  const providers = Array.isArray(data?.providers) ? data.providers : [];
  providerSelect.innerHTML = "";

  // opción "default" (dejar null en /api/ask)
  const optDefault = document.createElement("option");
  optDefault.value = "";
  optDefault.innerText = "(default)";
  providerSelect.appendChild(optDefault);

  for (const p of providers) {
    const opt = document.createElement("option");
    opt.value = p.name;
    opt.innerText = p.default ? `${p.name} (default)` : p.name;
    providerSelect.appendChild(opt);
  }

  if (!keepSelection) {
    providerSelect.value = selectedProvider || "";
  }

  providerSelect.onchange = () => {
    selectedProvider = String(providerSelect.value || "");
    selectedModel = ""; // reset model al cambiar provider
    localStorage.setItem("modia_provider", selectedProvider);
    localStorage.setItem("modia_model", selectedModel);
    populateModels(providers);
    renderCurrentModel();
  };

  populateModels(providers);
  renderCurrentModel();
}

function populateModels(providers) {
  if (!modelSelect) return;
  const providerName = String(providerSelect?.value || "");
  const provider = providers.find((p) => p.name === providerName);
  const models = Array.isArray(provider?.models) ? provider.models : [];

  modelSelect.innerHTML = "";
  const optDefault = document.createElement("option");
  optDefault.value = "";
  optDefault.innerText = "(default)";
  modelSelect.appendChild(optDefault);

  for (const m of models) {
    const opt = document.createElement("option");
    opt.value = m;
    opt.innerText = m;
    modelSelect.appendChild(opt);
  }

  modelSelect.value = selectedModel || "";
  modelSelect.onchange = () => {
    selectedModel = String(modelSelect.value || "");
    localStorage.setItem("modia_model", selectedModel);
    renderCurrentModel();
  };
}

async function refreshRepos() {
  if (!repoList) return;
  const res = await fetch("/api/repos");
  const data = await safeJson(res);
  if (!res.ok) {
    repoList.innerText = data?.detail || `No se pudo leer repos (HTTP ${res.status})`;
    return;
  }
  const urls = Array.isArray(data?.urls) ? data.urls : [];
  repoList.innerText = urls.length ? urls.join("\n") : "Sin repos adicionales.";
}

async function refreshDbStats() {
  if (!dbStatsText) return;
  const res = await fetch("/api/db/stats");
  const data = await safeJson(res);
  if (!res.ok) {
    dbStatsText.innerText = data?.detail || `No se pudo leer stats (HTTP ${res.status})`;
    return;
  }
  dbStatsText.innerText = `Docs: ${data?.total_documents ?? "?"} · Embeddings: ${data?.embedding_model ?? "?"}`;
}

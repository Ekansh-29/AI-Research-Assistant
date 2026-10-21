// Where the backend lives.
// "" = same server that serves this page (local and Render setup).
// If the frontend is ever hosted separately, put the backend URL here.
const API_BASE = "";

const $ = (sel) => document.querySelector(sel);

// ---------------------------------------------------------------
// Small helper for calling the backend
// ---------------------------------------------------------------
async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, options);
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }

  if (!res.ok) {
    let detail = data && data.detail;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join(", ");
    const err = new Error(detail || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ---------------------------------------------------------------
// Admin login
//   - If the server has no password: everyone can upload/delete.
//   - If it has one: visitors see only the chat and paper list;
//     after "Unlock", the password box disappears and admin tools show.
// The password is kept for this browser tab only (sessionStorage).
// ---------------------------------------------------------------
const state = {
  adminRequired: true,   // assume locked until the server says otherwise
  adminToken: "",
  maxUploadMb: 15,
};

function canEdit() {
  return !state.adminRequired || Boolean(state.adminToken);
}

function adminHeaders() {
  return state.adminToken ? { "X-Admin-Token": state.adminToken } : {};
}

function saveToken(token) {
  state.adminToken = token;
  try {
    if (token) sessionStorage.setItem("adminToken", token);
    else sessionStorage.removeItem("adminToken");
  } catch { /* storage blocked: still works until page reload */ }
}

function readSavedToken() {
  try { return sessionStorage.getItem("adminToken") || ""; } catch { return ""; }
}

function renderAdminUI() {
  const editing = canEdit();
  $("#upload-form").hidden = !editing;
  $("#admin-badge").hidden = !(state.adminRequired && state.adminToken);
  $("#admin-login").hidden = !(state.adminRequired && !state.adminToken);
  loadDocuments(); // re-draw list so delete buttons appear/disappear
}

async function verifyToken(token) {
  await api("/api/admin/verify", { method: "POST", headers: { "X-Admin-Token": token } });
}

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#admin-token");
  const btn = $("#login-btn");
  const status = $("#login-status");
  const token = input.value;
  if (!token) return;

  btn.disabled = true;
  status.textContent = "Checking…";
  status.className = "status";

  try {
    await verifyToken(token);
    saveToken(token);
    input.value = "";                 // clear the box
    $("#admin-login").open = false;
    status.textContent = "";
    renderAdminUI();
  } catch (err) {
    status.textContent = err.status === 401 ? "Wrong password." : err.message;
    status.className = "status error";
  } finally {
    btn.disabled = false;
  }
});

$("#logout-btn").addEventListener("click", () => {
  saveToken("");
  setStatus("");
  renderAdminUI();
});

// If the server rejects our saved password (e.g. it was changed), log out.
function handleAuthError(err) {
  if (err.status === 401) {
    saveToken("");
    renderAdminUI();
    return true;
  }
  return false;
}

async function initAdmin() {
  try {
    const info = await api("/api/info");
    state.adminRequired = info.admin_required;
    state.maxUploadMb = info.max_upload_mb;
  } catch {
    // Backend unreachable: loadDocuments() will show the error.
  }

  const saved = readSavedToken();
  if (state.adminRequired && saved) {
    try {
      await verifyToken(saved);
      state.adminToken = saved;
    } catch {
      saveToken("");
    }
  }
  renderAdminUI();
}

// ---------------------------------------------------------------
// Documents (sidebar)
// ---------------------------------------------------------------
function setStatus(text, kind = "") {
  const el = $("#upload-status");
  el.textContent = text;
  el.className = "status " + kind;
}

async function loadDocuments() {
  const list = $("#doc-list");
  try {
    const docs = await api("/api/documents");
    list.innerHTML = "";

    if (docs.length === 0) {
      list.innerHTML = '<li class="empty">No papers indexed yet.</li>';
      return;
    }

    for (const doc of docs) {
      const li = document.createElement("li");

      const info = document.createElement("div");
      const name = document.createElement("div");
      name.className = "doc-name";
      name.textContent = doc.filename;
      const meta = document.createElement("div");
      meta.className = "doc-meta";
      meta.textContent = `${doc.pages} pages · ${doc.chunks} chunks · ${doc.indexed_at}`;
      info.append(name, meta);
      li.append(info);

      if (canEdit()) {
        const del = document.createElement("button");
        del.className = "delete-btn";
        del.textContent = "Delete";
        del.title = `Delete ${doc.filename}`;
        del.onclick = () => deleteDocument(doc.filename);
        li.append(del);
      }

      list.append(li);
    }
  } catch (err) {
    list.innerHTML = "";
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Couldn't reach the backend: " + err.message;
    list.append(li);
  }
}

async function deleteDocument(filename) {
  if (!confirm(`Delete "${filename}" and all its chunks?`)) return;
  try {
    await api(`/api/documents/${encodeURIComponent(filename)}`, {
      method: "DELETE",
      headers: adminHeaders(),
    });
    setStatus(`Deleted ${filename}`, "ok");
    loadDocuments();
  } catch (err) {
    if (!handleAuthError(err)) setStatus(err.message, "error");
  }
}

// ---------------------------------------------------------------
// Upload
// ---------------------------------------------------------------
const fileInput = $("#file-input");
const dropzone = $("#dropzone");
let selectedFile = null;

function pickFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    setStatus("Please choose a PDF file.", "error");
    return;
  }
  if (file.size > state.maxUploadMb * 1024 * 1024) {
    setStatus(`File is larger than ${state.maxUploadMb} MB.`, "error");
    return;
  }
  selectedFile = file;
  $("#file-label").textContent = file.name;
  $("#upload-btn").disabled = false;
  setStatus("");
}

fileInput.addEventListener("change", () => pickFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag"); })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("drag"); })
);
dropzone.addEventListener("drop", (e) => pickFile(e.dataTransfer.files[0]));

$("#upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  const btn = $("#upload-btn");
  btn.disabled = true;
  setStatus("Indexing… this can take a minute for big papers.");

  const form = new FormData();
  form.append("file", selectedFile);

  try {
    const stats = await api("/api/documents", {
      method: "POST",
      body: form,
      headers: adminHeaders(),
    });
    setStatus(`Indexed ${stats.chunks} chunks from ${stats.pages} pages.`, "ok");
    selectedFile = null;
    fileInput.value = "";
    $("#file-label").textContent = "Click or drop a research paper here";
    loadDocuments();
  } catch (err) {
    if (!handleAuthError(err)) {
      setStatus(err.message, "error");
      btn.disabled = false;
    }
  }
});

// ---------------------------------------------------------------
// Chat
// ---------------------------------------------------------------
const messages = $("#messages");
const questionBox = $("#question");

function addMessage(role, text, extraClass = "") {
  const welcome = messages.querySelector(".welcome");
  if (welcome) welcome.remove();

  const row = document.createElement("div");
  row.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble " + extraClass;
  bubble.textContent = text;           // textContent = safe, no HTML injection
  row.append(bubble);
  messages.append(row);
  messages.scrollTop = messages.scrollHeight;
  return { row, bubble };
}

function renderSources(bubble, sources, citations) {
  if (!sources.length) return;

  const box = document.createElement("details");
  box.className = "sources";
  const summary = document.createElement("summary");
  summary.textContent = "Sources: " + citations.join("  ·  ");
  box.append(summary);

  const ul = document.createElement("ul");
  for (const s of sources) {
    const li = document.createElement("li");
    li.textContent = `${s.source}, page ${s.page ?? "?"}`;
    const snip = document.createElement("span");
    snip.className = "snippet";
    snip.textContent = `"${s.snippet.trim()}…"`;
    li.append(snip);
    ul.append(li);
  }
  box.append(ul);
  bubble.append(box);
}

async function askQuestion() {
  const question = questionBox.value.trim();
  if (!question) return;

  addMessage("user", question);
  questionBox.value = "";
  autoGrow();

  const askBtn = $("#ask-btn");
  askBtn.disabled = true;
  const { row, bubble } = addMessage("assistant", "Thinking…", "thinking");

  try {
    const data = await api("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    bubble.classList.remove("thinking");
    bubble.textContent = data.answer;
    renderSources(bubble, data.sources, data.citations);
  } catch (err) {
    bubble.classList.remove("thinking");
    row.classList.add("error");
    bubble.textContent = err.message;
  } finally {
    askBtn.disabled = false;
    messages.scrollTop = messages.scrollHeight;
    questionBox.focus();
  }
}

$("#ask-form").addEventListener("submit", (e) => { e.preventDefault(); askQuestion(); });

// Enter = send, Shift+Enter = new line
questionBox.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askQuestion(); }
});

function autoGrow() {
  questionBox.style.height = "auto";
  questionBox.style.height = questionBox.scrollHeight + "px";
}
questionBox.addEventListener("input", autoGrow);

// Start
initAdmin();

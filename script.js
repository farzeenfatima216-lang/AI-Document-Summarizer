const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const askBtn = document.getElementById("askBtn");

const documentText = document.getElementById("documentText");
const summary = document.getElementById("summary");
const keyPoints = document.getElementById("keyPoints");
const conversationHistory = document.getElementById("conversationHistory");
const statusMessage = document.getElementById("statusMessage");
const chunkCount = document.getElementById("chunkCount");
const textLength = document.getElementById("textLength");
const questionInput = document.getElementById("question");

const state = {
  text: "",
  chunks: [],
  fileName: ""
};

function getApiBase() {
  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000";
  }

  if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
    return `${window.location.protocol}//${window.location.hostname}${window.location.port ? `:${window.location.port}` : ""}`;
  }

  return "http://127.0.0.1:8000";
}

const API_BASE = getApiBase();

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.style.color = isError ? "#ff8a8a" : "#90a3bf";
}

function renderAnalysis(data, fileName) {
  state.text = data.preview || "";
  state.chunks = data.chunks || [];
  state.fileName = fileName;

  documentText.textContent = state.text || "No readable content was extracted.";
  summary.innerHTML = `<p>${escapeHtml(data.summary || "No summary available.")}</p>`;
  keyPoints.innerHTML = (data.key_points || []).map((point) => `<li>${escapeHtml(point)}</li>`).join("");
  chunkCount.textContent = data.chunk_count || 0;
  textLength.textContent = data.text_length || 0;
  conversationHistory.innerHTML = "Ask a question about this document to get a focused answer.";
  questionInput.value = "";
  questionInput.focus();
}

async function readJsonResponse(response) {
  const text = await response.text();

  if (!text) {
    throw new Error(`The server returned an empty response (status ${response.status}).`);
  }

  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`The server returned invalid data: ${text.slice(0, 220)}`);
  }
}

uploadBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];

  if (!file) {
    setStatus("Please choose a PDF, DOCX, or text file first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setStatus("Analyzing document…");
  uploadBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      body: formData
    });

    const data = await readJsonResponse(response);
    if (!response.ok) {
      throw new Error(data.error || "Processing failed");
    }

    renderAnalysis(data, data.file_name || file.name);
    setStatus(`Processed ${state.fileName} successfully.`);
  } catch (error) {
    console.error("Upload failed", error);
    setStatus(error.message, true);
  } finally {
    uploadBtn.disabled = false;
  }
});

function addMessageToHistory(question, answer, isError = false) {
  // Clear initial message on first Q&A
  if (conversationHistory.textContent === "Ask a question about this document to get a focused answer.") {
    conversationHistory.innerHTML = "";
  }

  const messageDiv = document.createElement("div");
  messageDiv.className = "message-pair";
  messageDiv.innerHTML = `
    <div class="message question-message">
      <strong>Q:</strong> ${escapeHtml(question)}
    </div>
    <div class="message answer-message ${isError ? "error" : ""}">
      <strong>A:</strong> ${escapeHtml(answer)}
    </div>
  `;
  conversationHistory.appendChild(messageDiv);
  conversationHistory.scrollTop = conversationHistory.scrollHeight;
}

askBtn.addEventListener("click", async () => {
  const question = questionInput.value.trim();

  if (!question) {
    setStatus("Please enter a question first.", true);
    return;
  }

  if (!state.text) {
    setStatus("Upload and analyze a document before asking questions.", true);
    return;
  }

  setStatus("Generating an answer…");
  askBtn.disabled = true;
  questionInput.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        context: state.text,
        chunks: state.chunks
      })
    });

    const data = await readJsonResponse(response);
    if (!response.ok) {
      throw new Error(data.error || "Answer generation failed");
    }

    addMessageToHistory(question, data.answer || "No answer generated.");
    questionInput.value = "";
    questionInput.focus();
    setStatus("Answer ready.");
  } catch (error) {
    console.error("Question failed", error);
    addMessageToHistory(question, error.message, true);
    setStatus(error.message, true);
  } finally {
    askBtn.disabled = false;
    questionInput.disabled = false;
  }
});

// Allow Enter key to submit question
questionInput.addEventListener("keypress", (event) => {
  if (event.key === "Enter" && !askBtn.disabled) {
    askBtn.click();
  }
});
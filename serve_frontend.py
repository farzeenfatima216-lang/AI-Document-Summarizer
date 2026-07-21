import io
import json
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import SpooledTemporaryFile
from urllib.parse import parse_qs, urlparse

from utils import extract_text_from_file

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8000"))

try:
    import cgi  # type: ignore
except Exception:  # pragma: no cover - Python 3.13+
    cgi = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    from docx import Document
except Exception:  # pragma: no cover - optional dependency
    Document = None

try:
    from langchain_groq import ChatGroq
except Exception:  # pragma: no cover - optional dependency
    ChatGroq = None

LLM = None
if ChatGroq and os.getenv("GROQ_API_KEY"):
    try:
        LLM = ChatGroq(model_name="openai/gpt-oss-120b")
    except Exception:  # pragma: no cover - runtime safety
        LLM = None


def split_into_chunks(text, chunk_size=700):
    if not text.strip():
        return []
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > chunk_size and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def build_summary(text):
    if LLM:
        try:
            prompt = (
                "Summarize this document in 4 short bullet points.\n"
                + text[:8000]
            )
            response = LLM.invoke(prompt)
            summary = getattr(response, "content", str(response)).strip()
            if summary:
                return summary
        except Exception:
            pass

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        return " ".join(sentences[:3])
    return text[:300].strip() or "No readable text was found in the uploaded file."


def build_key_points(text):
    if LLM:
        try:
            prompt = (
                "Extract 5 concise and useful key points from this document.\n"
                + text[:8000]
            )
            response = LLM.invoke(prompt)
            content = getattr(response, "content", str(response)).strip()
            if content:
                return [line.strip(" -•") for line in content.splitlines() if line.strip()]
        except Exception:
            pass

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return ["No readable content found in the uploaded file."]
    points = []
    for sentence in sentences[:5]:
        points.append(sentence[:180] + ("..." if len(sentence) > 180 else ""))
    return points


def build_answer(question, context, chunks=None):
    if not question or not context:
        return "Please provide both a question and document content."

    if LLM:
        try:
            prompt = (
                "Answer the question using only the provided context.\n"
                f"Question: {question}\n"
                f"Context: {context[:12000]}"
            )
            response = LLM.invoke(prompt)
            answer = getattr(response, "content", str(response)).strip()
            if answer:
                return answer
        except Exception:
            pass

    keyword_tokens = [
        token for token in re.findall(r"[a-z0-9]+", question.lower()) if len(token) > 2
    ]
    if not keyword_tokens:
        return "Please ask a clearer question about the document."

    candidate_chunks = chunks or split_into_chunks(context)
    best_match = ""
    best_score = -1
    for chunk in candidate_chunks:
        lower_chunk = chunk.lower()
        score = sum(1 for token in keyword_tokens if token in lower_chunk)
        if score > best_score:
            best_score = score
            best_match = chunk

    if best_match:
        return best_match[:700].strip()

    return context[:700].strip() or "No relevant answer could be generated from the provided document."


def parse_form_data(body_bytes, content_type):
    if not body_bytes:
        return {}

    if "multipart/form-data" not in content_type:
        return {}

    boundary = None
    for part in content_type.split(";"):
        if part.strip().startswith("boundary="):
            boundary = part.split("=", 1)[1].strip().strip('"')
            break

    if not boundary:
        raise ValueError("Multipart boundary is missing from the request")

    boundary_bytes = boundary.encode("utf-8")
    raw_parts = body_bytes.split(b"--" + boundary_bytes)
    result = {}

    for raw_part in raw_parts:
        if not raw_part or raw_part in (b"--", b"--\r\n", b"\r\n"):
            continue

        chunk = raw_part.strip(b"\r\n")
        if not chunk:
            continue

        if b"\r\n\r\n" in chunk:
            header_bytes, data = chunk.split(b"\r\n\r\n", 1)
        elif b"\n\n" in chunk:
            header_bytes, data = chunk.split(b"\n\n", 1)
        else:
            continue

        headers = {}
        for line in header_bytes.splitlines():
            if b":" in line:
                key, value = line.split(b":", 1)
                headers[key.decode("latin-1").strip().lower()] = value.decode("latin-1").strip()

        disposition = headers.get("content-disposition", "")
        name = None
        filename = None
        for item in disposition.split(";"):
            item = item.strip()
            if item.startswith("name="):
                name = item.split("=", 1)[1].strip().strip('"')
            elif item.startswith("filename="):
                filename = item.split("=", 1)[1].strip().strip('"')

        if name is None:
            continue

        data_bytes = data.rstrip(b"\r\n")
        if name not in result:
            result[name] = type("FormValue", (), {})()

        value = result[name]
        value.name = name
        value.filename = filename
        value.file = SpooledTemporaryFile()
        value.file.write(data_bytes)
        value.file.seek(0)

    return result


def parse_urlencoded_form(body_bytes):
    if not body_bytes:
        return {}
    return {key: values[0] if len(values) == 1 else values for key, values in parse_qs(body_bytes.decode("utf-8")).items()}


def extract_text(file_name, file_bytes):
    return extract_text_from_file(file_name, file_bytes)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/analyze":
            self.send_json(405, {"error": "Use POST to upload a file."})
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/analyze":
            self.handle_analyze()
            return
        if parsed.path == "/api/ask":
            self.handle_ask()
            return
        self.send_error(404)

    def handle_analyze(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body_bytes = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "")

            if "multipart/form-data" in content_type:
                form = parse_form_data(body_bytes, content_type)
                file_item = form.get("file")
                if not file_item or not getattr(file_item, "file", None):
                    self.send_json(400, {"error": "No file uploaded. Please choose a PDF, DOCX, or text file first."})
                    return
                file_name = os.path.basename(file_item.filename or "uploaded_file")
                file_bytes = file_item.file.read()
            else:
                if cgi is not None:
                    form = cgi.FieldStorage(
                        fp=io.BytesIO(body_bytes),
                        headers=self.headers,
                        environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
                    )
                    file_item = form["file"] if "file" in form else None
                    if file_item is None or not getattr(file_item, "file", None):
                        self.send_json(400, {"error": "No file uploaded. Please choose a PDF, DOCX, or text file first."})
                        return
                    file_name = os.path.basename(file_item.filename or "uploaded_file")
                    file_bytes = file_item.file.read()
                else:
                    self.send_json(400, {"error": "No file uploaded. Please choose a PDF, DOCX, or text file first."})
                    return

            if isinstance(file_bytes, str):
                file_bytes = file_bytes.encode("utf-8")

            text = extract_text(file_name, file_bytes)
            chunks = split_into_chunks(text)
            summary = build_summary(text)
            key_points = build_key_points(text)

            payload = {
                "status": "success",
                "message": "File processed successfully",
                "file_name": file_name,
                "preview": text[:4000],
                "summary": summary,
                "key_points": key_points,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "text_length": len(text),
            }
            self.send_json(200, payload)
        except Exception as exc:  # noqa: BLE001
            self.send_json(500, {"error": f"Upload failed: {exc}"})

    def handle_ask(self):
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", "0"))
            body_bytes = self.rfile.read(content_length)

            if content_type.startswith("application/json"):
                raw_body = body_bytes.decode("utf-8")
                payload = json.loads(raw_body) if raw_body else {}
                question = payload.get("question", "")
                context = payload.get("context", "") or payload.get("text", "")
                chunks = payload.get("chunks", [])
            else:
                if cgi is not None:
                    form = cgi.FieldStorage(
                        fp=io.BytesIO(body_bytes),
                        headers=self.headers,
                        environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
                    )
                    question = form.getvalue("question", "")
                    context = form.getvalue("context", "")
                    chunks = form.getvalue("chunks", [])
                else:
                    form = parse_urlencoded_form(body_bytes)
                    question = form.get("question", "")
                    context = form.get("context", "")
                    chunks = form.get("chunks", [])

            answer = build_answer(question, context, chunks)
            self.send_json(200, {"status": "success", "answer": answer, "question": question})
        except Exception as exc:  # noqa: BLE001
            self.send_json(500, {"error": str(exc)})

    def send_json(self, status_code, payload):
        try:
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            body = json.dumps({"error": str(exc)}).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving frontend and backend at http://127.0.0.1:{PORT}/")
        httpd.serve_forever()

import io
import os
import re
import zipfile
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    from docx import Document
except Exception:  # pragma: no cover - optional dependency
    Document = None


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".json"}


def normalize_filename(name: Optional[str]) -> str:
    if not name:
        return "uploaded_file"
    return Path(name).name


def extract_text_from_file(file_name: Optional[str], file_bytes: bytes) -> str:
    name = normalize_filename(file_name).lower()

    if name.endswith((".txt", ".md", ".json")):
        return file_bytes.decode("utf-8", errors="ignore").strip()

    if name.endswith(".pdf"):
        if PdfReader is None:
            raise RuntimeError("PDF support requires pypdf. Install it with pip install pypdf")
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text:
                pages.append(text)
        return "\n".join(pages).strip()

    if name.endswith(".docx"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                candidate_names = [
                    "word/document.xml",
                    "word/footnotes.xml",
                    "word/endnotes.xml",
                ]
                for candidate in candidate_names:
                    if candidate in archive.namelist():
                        xml_bytes = archive.read(candidate)
                        text = re.sub(r"<[^>]+>", " ", xml_bytes.decode("utf-8", errors="ignore"))
                        text = re.sub(r"\s+", " ", text).strip()
                        if text:
                            return text
        except Exception:
            pass

        if Document is not None:
            try:
                document = Document(io.BytesIO(file_bytes))
                paragraphs = [
                    para.text.strip()
                    for para in document.paragraphs
                    if para.text and para.text.strip()
                ]
                return "\n".join(paragraphs).strip()
            except Exception as exc:
                raise RuntimeError(f"DOCX parsing failed: {exc}") from exc

        raise RuntimeError("DOCX parsing failed because the file is not a valid Word document")

    raise ValueError("Unsupported file type. Use txt, md, json, pdf, or docx.")


def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    if not text or not text.strip():
        return []

    words = re.split(r"\s+", text.strip())
    if not words:
        return []

    chunks = []
    current = []
    current_len = 0

    for word in words:
        if current and current_len + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1

    if current:
        chunks.append(" ".join(current))

    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped = []
        for index, chunk in enumerate(chunks):
            if index == 0:
                overlapped.append(chunk)
            else:
                previous = chunks[index - 1]
                overlap_words = previous.split()[-chunk_overlap // 5:]
                overlapped.append(" ".join(overlap_words + chunk.split()))
        return overlapped

    return chunks


def prepare_document_payload(file_name: Optional[str], file_bytes: bytes) -> dict:
    text = extract_text_from_file(file_name, file_bytes)
    chunks = split_text_into_chunks(text)
    return {
        "text": text,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "text_length": len(text),
    }

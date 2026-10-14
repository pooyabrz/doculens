"""Read documents without writing uploaded files to disk."""

import hashlib
import re
from io import BytesIO
from pathlib import PurePosixPath

from pypdf import PdfReader

from doculens.models import Chunk, Document

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 200
MAX_TEXT_CHARS = 800_000
MAX_CHUNKS = 1_200


class DocumentError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def split_text(text: str, size: int = 1_000, overlap: int = 120) -> list[str]:
    """Keep short paragraphs whole; overlap windows of long paragraphs."""
    if size < 32 or not 0 <= overlap < size // 2:
        raise ValueError("Invalid chunk size or overlap.")
    result: list[str] = []
    for paragraph in re.split(r"\n[ \t]*\n+", text.replace("\r\n", "\n")):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        start = 0
        while start < len(paragraph):
            end = min(start + size, len(paragraph))
            if end < len(paragraph):
                boundary = max(
                    paragraph.rfind(" ", start + size // 2, end),
                    paragraph.rfind("\n", start + size // 2, end),
                )
                if boundary > start:
                    end = boundary
            piece = paragraph[start:end].strip()
            if piece:
                result.append(piece)
            if end == len(paragraph):
                break
            start = max(start + 1, end - overlap)
    return result


def load_document(filename: str, data: bytes) -> Document:
    """Use physical PDF page numbers; text files have passage numbers only."""
    safe_name = PurePosixPath(filename.replace("\\", "/")).name[:180]
    suffix = PurePosixPath(safe_name).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise DocumentError("unsupported", "Use a PDF, UTF-8 TXT, or Markdown file.")
    if not data:
        raise DocumentError("empty", "The file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise DocumentError("too_large", "Each file must be at most 10 MiB.")

    document_id = hashlib.sha256(data).hexdigest()
    pages: list[tuple[int | None, str]] = []
    warnings: list[str] = []
    if suffix == ".pdf":
        if b"%PDF-" not in data[:1024]:
            raise DocumentError("invalid_pdf", "This file does not have a PDF header.")
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted and not reader.decrypt(""):
                raise DocumentError("encrypted", "Password-protected PDFs are not supported.")
            if len(reader.pages) > MAX_PAGES:
                raise DocumentError("too_many_pages", "PDFs may contain at most 200 pages.")
            total_chars = 0
            for number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                total_chars += len(text)
                if total_chars > MAX_TEXT_CHARS:
                    raise DocumentError("too_much_text", "Extracted text exceeds the limit.")
                if not text.strip():
                    warnings.append(f"Page {number}: no extractable text; OCR may be needed.")
                pages.append((number, text))
        except DocumentError:
            raise
        except Exception as exc:
            raise DocumentError("invalid_pdf", "The PDF could not be read.") from exc
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentError("encoding", "Text files must use UTF-8 encoding.") from exc
        if "\x00" in text:
            raise DocumentError("encoding", "The file contains binary or UTF-16 data.")
        if len(text) > MAX_TEXT_CHARS:
            raise DocumentError("too_much_text", "The text exceeds the size limit.")
        pages.append((None, text))

    chunks: list[Chunk] = []
    for page_number, text in pages:
        for passage, part in enumerate(split_text(text), start=1):
            chunks.append(
                Chunk(
                    id=f"{document_id}:{page_number or 0}:{passage}",
                    document_id=document_id,
                    filename=safe_name,
                    text=part,
                    passage=passage,
                    page=page_number,
                )
            )
            if len(chunks) > MAX_CHUNKS:
                raise DocumentError("too_many_chunks", "The document has too many passages.")
    if not chunks:
        raise DocumentError("no_text", "No text was found. Scanned PDFs need OCR.")
    return Document(document_id, safe_name, tuple(chunks), tuple(warnings))

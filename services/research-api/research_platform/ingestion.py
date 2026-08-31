import json
from hashlib import sha256
from pathlib import Path

from pypdf import PdfReader

from .models import Chunk


def file_hash(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_text(text, size=900, overlap=120):
    if size <= overlap or overlap < 0:
        raise ValueError("invalid chunk settings")
    normalized = " ".join((text or "").split())
    return [
        normalized[start : start + size]
        for start in range(0, len(normalized), size - overlap)
        if normalized[start : start + size]
    ]


def ingest_pdf(path, document_id, *, chunk_size=900, overlap=120, ocr_adapter=None):
    source = Path(path)
    if source.suffix.lower() != ".pdf" or not source.exists():
        raise ValueError("a readable PDF is required")
    version = file_hash(source)
    reader = PdfReader(source)
    chunks, page_audit = [], []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        ocr_derived, error = False, None
        if not text.strip() and ocr_adapter:
            try:
                text = ocr_adapter.extract(source, page_number)
                ocr_derived = True
            except Exception:
                error = "OCR failed"
        if not text.strip() and error is None:
            error = "No text layer; OCR required"
        page_audit.append(
            {
                "page_number": page_number,
                "has_text_layer": bool((page.extract_text() or "").strip()),
                "ocr_derived": ocr_derived,
                "error": error,
            }
        )
        for index, value in enumerate(split_text(text, chunk_size, overlap)):
            chunks.append(
                Chunk(
                    document_id,
                    version,
                    page_number,
                    f"{document_id}:{version[:8]}:{page_number}:{index}",
                    value,
                    ocr_derived=ocr_derived,
                )
            )
    return {
        "document_id": document_id,
        "document_version": version,
        "path": str(source),
        "chunks": chunks,
        "page_audit": page_audit,
    }


def write_index(documents, path):
    versions = {}
    records = []
    for document in documents:
        versions[document["document_id"]] = document["document_version"]
        records.extend(chunk.to_dict() for chunk in document["chunks"])
    payload = {"format_version": 1, "document_versions": versions, "records": records}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload

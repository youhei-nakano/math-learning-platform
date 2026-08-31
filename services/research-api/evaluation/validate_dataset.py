import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_platform.ingestion import file_hash, ingest_pdf

CASE_FIELDS = {
    "question_id",
    "question",
    "domain",
    "difficulty",
    "answer_type",
    "answerable",
    "expected_answer",
    "acceptable_variants",
    "grading_rubric",
    "required_reasoning",
    "source_document_ids",
    "source_pages",
    "required_chunk_ids",
    "expected_citations",
    "dataset_version",
    "auto_gradable",
}


def validate_dataset(path):
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    errors = []
    cases = payload.get("cases", [])
    if len(cases) < 20:
        errors.append("dataset must contain at least 20 cases")
    identifiers = [case.get("question_id") for case in cases]
    if len(set(identifiers)) != len(identifiers):
        errors.append("question_id values must be unique")
    documents = {item.get("id"): item for item in payload.get("documents", [])}
    chunk_ids = set()
    page_counts = {}
    for document_id, document in documents.items():
        pdf = ROOT / document.get("path", "")
        if not pdf.exists():
            errors.append(f"missing PDF: {document_id}")
            continue
        if file_hash(pdf) != document.get("sha256"):
            errors.append(f"PDF hash mismatch: {document_id}")
            continue
        ingested = ingest_pdf(pdf, document_id)
        chunk_ids.update(chunk.chunk_id for chunk in ingested["chunks"])
        page_counts[document_id] = len(ingested["page_audit"])
    for case in cases:
        case_id = case.get("question_id", "<missing>")
        missing = CASE_FIELDS - set(case)
        if missing:
            errors.append(f"{case_id}: missing {sorted(missing)}")
        if case.get("dataset_version") != payload.get("version"):
            errors.append(f"{case_id}: dataset_version mismatch")
        if case.get("difficulty") not in {"easy", "medium", "hard"}:
            errors.append(f"{case_id}: invalid difficulty")
        for evidence in case.get("source_pages", []) + case.get(
            "expected_citations", []
        ):
            document_id = evidence.get("document_id")
            page = evidence.get("page_number")
            if document_id not in documents or not 1 <= int(
                page or 0
            ) <= page_counts.get(document_id, 0):
                errors.append(f"{case_id}: invalid evidence page {evidence}")
        unknown_chunks = set(case.get("required_chunk_ids", [])) - chunk_ids
        if unknown_chunks:
            errors.append(f"{case_id}: unknown chunks {sorted(unknown_chunks)}")
    if sum(not case.get("answerable", True) for case in cases) < 2:
        errors.append("dataset must include at least two unanswerable cases")
    if len({case.get("domain") for case in cases}) < 8:
        errors.append("dataset must cover at least eight domains")
    if set(case.get("difficulty") for case in cases) != {"easy", "medium", "hard"}:
        errors.append("dataset must cover all difficulty levels")
    summary = {
        "version": payload.get("version"),
        "cases": len(cases),
        "documents": len(documents),
        "answerable": sum(case.get("answerable", True) for case in cases),
        "unanswerable": sum(not case.get("answerable", True) for case in cases),
        "domains": dict(Counter(case.get("domain") for case in cases)),
        "difficulties": dict(Counter(case.get("difficulty") for case in cases)),
        "valid": not errors,
        "errors": errors,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    args = parser.parse_args()
    summary = validate_dataset(args.dataset)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary["valid"] else 1)


if __name__ == "__main__":
    main()

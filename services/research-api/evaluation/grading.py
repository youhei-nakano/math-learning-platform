import re
from decimal import Decimal, InvalidOperation

DECLINE_MARKERS = (
    "資料内では確認できません",
    "資料にありません",
    "cannot determine",
    "can't determine",
    "can’t determine",
    "cannot be answered",
    "unanswerable",
    "not in the provided",
    "insufficient information",
    "insufficient evidence",
)


def normalize_text(value):
    value = str(value or "").strip().lower()
    value = value.replace("−", "-").replace("×", "*").replace("÷", "/")
    return re.sub(r"\s+", "", value).strip(".,;:$")


def _number(value):
    match = re.fullmatch(r"[-+]?\d+(?:\.\d+)?", normalize_text(value))
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def grade_answer(case, answer):
    text = str(answer or "")
    if not case.get("answerable", True):
        correct = any(marker in text.lower() for marker in DECLINE_MARKERS)
        return {"correct": correct, "kind": "unanswerable-decline"}

    candidates = [case.get("expected_answer", case.get("answer", ""))]
    candidates.extend(case.get("acceptable_variants", []))
    answer_normalized = normalize_text(text)
    for candidate in candidates:
        candidate_normalized = normalize_text(candidate)
        expected_number = _number(candidate)
        found_numbers = [
            _number(item) for item in re.findall(r"[-+]?\d+(?:\.\d+)?", text)
        ]
        if expected_number is not None and expected_number in found_numbers:
            return {"correct": True, "kind": "numeric-exact"}
        if candidate_normalized and candidate_normalized in answer_normalized:
            return {"correct": True, "kind": "normalized-match"}
    return {"correct": False, "kind": "deterministic-no-match"}


def citation_scores(actual, expected):
    actual_set = {(item.get("document_id"), item.get("page_number")) for item in actual}
    expected_set = {
        (item.get("document_id"), item.get("page_number")) for item in expected
    }
    return {
        "precision": len(actual_set & expected_set) / len(actual_set)
        if actual_set
        else (1.0 if not expected_set else 0.0),
        "recall": len(actual_set & expected_set) / len(expected_set)
        if expected_set
        else 1.0,
    }

import re
import time
from datetime import datetime, timezone
from hashlib import sha256

from .retrieval import rerank, search

MAX_QUERIES = 4
MAX_TOP_K = 8
MODES = {"keyword", "vector", "hybrid"}

COORDINATOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "problem_type": {"type": "string"},
        "domain": {"type": "string"},
        "difficulty_hypothesis": {
            "type": "string",
            "enum": ["easy", "medium", "hard", "unknown"],
        },
        "subproblems": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["id", "description"],
            },
        },
        "required_evidence": {"type": "array", "items": {"type": "string"}},
        "required_operations": {"type": "array", "items": {"type": "string"}},
        "answerability_hypothesis": {
            "type": "string",
            "enum": ["answerable", "unanswerable", "uncertain"],
        },
        "retrieval_needed": {"type": "boolean"},
        "constraints": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "problem_type",
        "domain",
        "difficulty_hypothesis",
        "subproblems",
        "required_evidence",
        "required_operations",
        "answerability_hypothesis",
        "retrieval_needed",
        "constraints",
    ],
}

RETRIEVER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query_id": {"type": "string"},
                    "text": {"type": "string"},
                    "intent": {"type": "string"},
                    "subproblem_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "filters": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "document_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "pages": {"type": "array", "items": {"type": "integer"}},
                        },
                        "required": ["document_ids", "pages"],
                    },
                },
                "required": [
                    "query_id",
                    "text",
                    "intent",
                    "subproblem_ids",
                    "filters",
                ],
            },
        },
        "search_mode": {"type": "string", "enum": sorted(MODES)},
        "top_k": {"type": "integer"},
        "rerank": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
    "required": ["queries", "search_mode", "top_k", "rerank", "rationale"],
}

SOLVER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answerable": {"type": "boolean"},
        "answer": {"type": "string"},
        "reasoning_summary": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
        "citation_ids": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "answerable",
        "answer",
        "reasoning_summary",
        "steps",
        "citation_ids",
        "uncertainties",
    ],
}

VERIFIER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "revise", "reject"]},
        "answer_correctness": {
            "type": "string",
            "enum": ["pass", "fail", "uncertain"],
        },
        "citation_validity": {
            "type": "string",
            "enum": ["pass", "fail", "uncertain"],
        },
        "citation_support": {
            "type": "string",
            "enum": ["pass", "fail", "uncertain"],
        },
        "answerability": {
            "type": "string",
            "enum": ["answerable", "unanswerable", "uncertain"],
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "math",
                            "logic",
                            "citation",
                            "answerability",
                            "completeness",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "description": {"type": "string"},
                },
                "required": ["type", "severity", "description"],
            },
        },
        "permitted_citation_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
        "revision_instructions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "corrected_answer": {"type": ["string", "null"]},
    },
    "required": [
        "verdict",
        "answer_correctness",
        "citation_validity",
        "citation_support",
        "answerability",
        "issues",
        "permitted_citation_ids",
        "revision_instructions",
        "corrected_answer",
    ],
}

TUTOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answerable": {"type": "boolean"},
        "final_answer": {"type": "string"},
        "citation_ids": {"type": "array", "items": {"type": "string"}},
        "uncertainty": {"type": ["string", "null"]},
    },
    "required": ["answerable", "final_answer", "citation_ids", "uncertainty"],
}

SINGLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answerable": {"type": "boolean"},
        "answer": {"type": "string"},
        "explanation": {"type": "string"},
        "citation_chunk_ids": {"type": "array", "items": {"type": "string"}},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "answerable",
        "answer",
        "explanation",
        "citation_chunk_ids",
        "issues",
    ],
}

ROLE_SCHEMAS = {
    "single": SINGLE_SCHEMA,
    "coordinator": COORDINATOR_SCHEMA,
    "retriever": RETRIEVER_SCHEMA,
    "solver": SOLVER_SCHEMA,
    "verifier": VERIFIER_SCHEMA,
    "tutor": TUTOR_SCHEMA,
}


def validate_shape(role, value):
    if not isinstance(value, dict):
        raise ValueError(f"{role} output must be an object")
    missing = set(ROLE_SCHEMAS[role]["required"]) - set(value)
    if missing:
        raise ValueError(f"{role} output missing {sorted(missing)}")
    return value


def validate_coordinator(plan):
    validate_shape("coordinator", plan)
    subproblems = plan["subproblems"]
    if not 1 <= len(subproblems) <= 8:
        raise ValueError("coordinator must produce 1 to 8 subproblems")
    identifiers = [item["id"].strip() for item in subproblems]
    if any(not value for value in identifiers) or len(set(identifiers)) != len(
        identifiers
    ):
        raise ValueError("subproblem IDs must be non-empty and unique")
    return plan


def validate_retrieval_plan(plan, document_ids):
    validate_shape("retriever", plan)
    queries = plan["queries"]
    if not 1 <= len(queries) <= MAX_QUERIES:
        raise ValueError(f"queries must contain 1 to {MAX_QUERIES} items")
    if plan["search_mode"] not in MODES:
        raise ValueError("unsupported search mode")
    if not 1 <= plan["top_k"] <= MAX_TOP_K:
        raise ValueError(f"top_k must be between 1 and {MAX_TOP_K}")
    seen = set()
    normalized = []
    for item in queries:
        query_id = item["query_id"].strip()
        text = " ".join(item["text"].split())
        if not query_id or query_id in seen or not text:
            raise ValueError("query IDs must be unique and query text cannot be empty")
        seen.add(query_id)
        filters = item["filters"]
        unknown = set(filters["document_ids"]) - set(document_ids)
        if unknown:
            raise ValueError(f"unknown document IDs: {sorted(unknown)}")
        pages = filters["pages"]
        if any(not isinstance(page, int) or page < 1 for page in pages):
            raise ValueError("page filters must be positive integers")
        normalized.append({**item, "query_id": query_id, "text": text})
    return {**plan, "queries": normalized}


def execute_retrieval(plan, chunks):
    plan = validate_retrieval_plan(plan, {chunk.document_id for chunk in chunks})
    started = time.perf_counter()
    query_runs = []
    combined = {}
    for query in plan["queries"]:
        filtered = [
            chunk
            for chunk in chunks
            if (
                not query["filters"]["document_ids"]
                or chunk.document_id in query["filters"]["document_ids"]
            )
            and (
                not query["filters"]["pages"]
                or chunk.page_number in query["filters"]["pages"]
            )
        ]
        candidates = search(
            filtered,
            query["text"],
            plan["search_mode"],
            plan["top_k"],
            min(MAX_TOP_K * 2, max(plan["top_k"], 1) * 2),
        )
        before = [hit.chunk.chunk_id for hit in candidates]
        final = (
            rerank(candidates, query["text"], plan["top_k"])
            if plan["rerank"]
            else candidates[: plan["top_k"]]
        )
        records = []
        for rank, hit in enumerate(final, 1):
            record = {
                "query_id": query["query_id"],
                "document_id": hit.chunk.document_id,
                "document_version": hit.chunk.document_version,
                "page_number": hit.chunk.page_number,
                "chunk_id": hit.chunk.chunk_id,
                "text": hit.chunk.text,
                "score": hit.rerank_score
                if hit.rerank_score is not None
                else hit.score,
                "rank": rank,
                "search_mode": plan["search_mode"],
                "ocr_derived": hit.chunk.ocr_derived,
            }
            records.append(record)
            existing = combined.get(hit.chunk.chunk_id)
            if existing is None or record["score"] > existing["score"]:
                combined[hit.chunk.chunk_id] = record
        query_runs.append(
            {
                "query": query,
                "normalized_query": query["text"],
                "rerank_before": before,
                "rerank_after": [item["chunk_id"] for item in records],
                "hits": records,
            }
        )
    evidence = sorted(
        combined.values(), key=lambda item: (-item["score"], item["chunk_id"])
    )[:MAX_TOP_K]
    return {
        "search_mode": plan["search_mode"],
        "top_k": plan["top_k"],
        "rerank": plan["rerank"],
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "query_runs": query_runs,
        "evidence": evidence,
    }


def enforce_solver_citations(solver, evidence_ids):
    validate_shape("solver", solver)
    unknown = set(solver["citation_ids"]) - set(evidence_ids)
    if unknown:
        raise ValueError(f"solver used unretrieved citations: {sorted(unknown)}")
    return solver


def enforce_verifier(verifier, evidence_ids):
    validate_shape("verifier", verifier)
    unknown = set(verifier["permitted_citation_ids"]) - set(evidence_ids)
    if unknown:
        raise ValueError(f"verifier permitted unknown citations: {sorted(unknown)}")
    unresolved = [
        issue for issue in verifier["issues"] if issue["severity"] in {"medium", "high"}
    ]
    if verifier["verdict"] == "pass" and unresolved:
        raise ValueError("pass verdict cannot contain medium/high unresolved issues")
    return verifier


def enforce_tutor(tutor, verifier):
    validate_shape("tutor", tutor)
    unknown = set(tutor["citation_ids"]) - set(verifier["permitted_citation_ids"])
    if unknown:
        raise ValueError(f"tutor added unpermitted citations: {sorted(unknown)}")
    if verifier["verdict"] == "reject" and tutor["answerable"]:
        raise ValueError("tutor revived a rejected answer")
    return tutor


def hit_difference(initial_ids, final_ids):
    left, right = set(initial_ids), set(final_ids)
    return {
        "added": sorted(right - left),
        "removed": sorted(left - right),
        "changed": left != right,
    }


def assess_revision(
    solver,
    tutor,
    before_correct,
    after_correct,
    expected_answerable=None,
    solver_citation_precision=None,
    tutor_citation_precision=None,
):
    answer_changed = solver["answer"].strip() != tutor["final_answer"].strip()
    citation_difference = {
        "added": sorted(set(tutor["citation_ids"]) - set(solver["citation_ids"])),
        "removed": sorted(set(solver["citation_ids"]) - set(tutor["citation_ids"])),
    }
    if not before_correct and after_correct:
        classification = "improved"
    elif before_correct and not after_correct:
        classification = "regressed"
    elif before_correct == after_correct and not answer_changed:
        classification = "unchanged"
    else:
        classification = "inconclusive"
    solver_answerability_correct = (
        solver["answerable"] == expected_answerable
        if expected_answerable is not None
        else None
    )
    tutor_answerability_correct = (
        tutor["answerable"] == expected_answerable
        if expected_answerable is not None
        else None
    )
    if solver_answerability_correct is False and tutor_answerability_correct is True:
        answerability_change = "improved"
    elif solver_answerability_correct is True and tutor_answerability_correct is False:
        answerability_change = "regressed"
    else:
        answerability_change = "unchanged"
    return {
        "classification": classification,
        "solver_correct": before_correct,
        "tutor_correct": after_correct,
        "answer_changed": answer_changed,
        "citation_difference": citation_difference,
        "answerability_change": answerability_change,
        "solver_citation_precision": solver_citation_precision,
        "tutor_citation_precision": tutor_citation_precision,
        "incorrect_citation_removed": (
            solver_citation_precision is not None
            and tutor_citation_precision is not None
            and tutor_citation_precision > solver_citation_precision
        ),
        "correct_citation_removed": (
            solver_citation_precision is not None
            and tutor_citation_precision is not None
            and tutor_citation_precision < solver_citation_precision
        ),
    }


def trace_step(
    experiment_id,
    question_id,
    role,
    started_at,
    duration_ms,
    input_payload,
    output,
    model=None,
    usage=None,
    status="success",
    error_code=None,
    mode="multi-pipeline-v2",
):
    safe_input = repr(input_payload).encode()
    return {
        "trace_id": sha256(
            f"{experiment_id}:{question_id}:{role}:{started_at}".encode()
        ).hexdigest()[:20],
        "experiment_id": experiment_id,
        "question_id": question_id,
        "mode": mode,
        "role": role,
        "started_at": started_at,
        "duration_ms": round(duration_ms, 3),
        "input_hash": sha256(safe_input).hexdigest(),
        "output": output,
        "model": model,
        "usage": usage or {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
        "status": status,
        "error_code": error_code,
    }


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def contains_secret(value):
    return bool(
        re.search(r"sk-[A-Za-z0-9_-]{20,}|authorization|api[_-]?key", repr(value), re.I)
    )


def validate_trace(trace, question_id):
    expected_roles = [
        "coordinator",
        "retriever",
        "search",
        "solver",
        "verifier",
        "tutor",
    ]
    roles = [item.get("role") for item in trace]
    if roles != expected_roles:
        raise ValueError(f"incomplete pipeline trace: {roles}")
    required = {
        "trace_id",
        "experiment_id",
        "question_id",
        "mode",
        "role",
        "started_at",
        "duration_ms",
        "input_hash",
        "output",
        "model",
        "usage",
        "status",
        "error_code",
    }
    for item in trace:
        if required - set(item):
            raise ValueError("trace step is missing required fields")
        if item["question_id"] != question_id or item["mode"] != "multi-pipeline-v2":
            raise ValueError("trace identity mismatch")
        if contains_secret(item):
            raise ValueError("secret-like data detected in trace")
    return trace

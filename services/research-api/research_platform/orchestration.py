import time

from .citations import format_citation, validate_citations
from .models import RunResult
from .retrieval import rerank, search


def _retrieve(case, chunks, config):
    hits = search(
        chunks,
        case["question"],
        config.retrieval,
        config.top_k,
        config.rerank_candidates if config.rerank else None,
    )
    return (
        rerank(hits, case["question"], config.top_k)
        if config.rerank
        else hits[: config.top_k]
    )


def _extractive_answer(hits):
    if not hits:
        return "資料内では確認できません。", []
    hit = hits[0]
    answer = f"{hit.chunk.text} {format_citation(hit.chunk)}"
    return answer, [
        {
            "document_id": hit.chunk.document_id,
            "page_number": hit.chunk.page_number,
            "chunk_id": hit.chunk.chunk_id,
        }
    ]


def run_case(case, chunks, config, experiment_id):
    config.validate()
    started = time.perf_counter()
    trace = []
    try:
        if config.mode == "single":
            hits = _retrieve(case, chunks, config)
            trace.append(
                {"agent": "single", "action": "retrieve_and_answer", "hits": len(hits)}
            )
            answer, citations = _extractive_answer(hits)
            steps, calls = 1, 1
        else:
            trace.append(
                {
                    "agent": "coordinator",
                    "action": "plan",
                    "goal": case["question"][:120],
                }
            )
            hits = _retrieve(case, chunks, config)
            trace.append({"agent": "retriever", "action": "search", "hits": len(hits)})
            answer, citations = _extractive_answer(hits)
            trace.append({"agent": "solver_tutor", "action": "explain"})
            verification = validate_citations(answer, hits)
            trace.append(
                {
                    "agent": "verifier",
                    "action": "verify",
                    "valid": verification["valid"],
                }
            )
            if not verification["valid"]:
                raise ValueError("citation verification failed")
            steps, calls = 4, 2
        if steps > config.max_steps:
            raise TimeoutError("maximum step count exceeded")
        return RunResult(
            case["id"],
            experiment_id,
            "success",
            answer,
            citations,
            round(time.perf_counter() - started, 6),
            calls,
            steps,
            trace=trace,
        )
    except Exception as error:
        return RunResult(
            case["id"],
            experiment_id,
            "failed",
            "",
            [],
            round(time.perf_counter() - started, 6),
            0,
            len(trace),
            error=type(error).__name__,
            trace=trace,
        )

"""Local, keyless HTTP boundary for the offline research corpus.

This server intentionally exposes only the generated CC0 demo dataset. It does
not accept PDF uploads, execute instructions found in documents, or call an
external model.
"""

import argparse
import json
import time
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from research_platform.citations import format_citation, validate_citations
from research_platform.config import ExperimentConfig
from research_platform.ingestion import ingest_pdf
from research_platform.orchestration import _retrieve

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "evaluation/datasets/demo-v1/dataset.json"
MAX_BODY_BYTES = 32 * 1024
DOCUMENT_TITLES = {
    "linear-foundations": "Linear Algebra Foundations",
    "calculus-foundations": "Calculus Foundations",
}


def load_corpus(dataset_path=DATASET_PATH):
    dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    chunks = []
    for document in dataset["documents"]:
        ingested = ingest_pdf(ROOT / document["path"], document["id"])
        if ingested["document_version"] != document["sha256"]:
            raise ValueError(f"document version mismatch: {document['id']}")
        chunks.extend(ingested["chunks"])
    return dataset, chunks


def validate_request(payload):
    if not isinstance(payload, dict):
        raise ValueError("JSON object is required")
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > 2_000:
        raise ValueError("question must contain 1-2000 characters")
    mode = payload.get("mode", "single")
    retrieval = payload.get("retrieval", "hybrid")
    top_k = payload.get("topK", 3)
    if mode not in {"single", "multi"}:
        raise ValueError("mode must be single or multi")
    if retrieval not in {"keyword", "vector", "hybrid"}:
        raise ValueError("unsupported retrieval mode")
    if not isinstance(top_k, int) or not 1 <= top_k <= 8:
        raise ValueError("topK must be an integer from 1 to 8")
    return question.strip(), ExperimentConfig(
        mode=mode,
        retrieval=retrieval,
        top_k=top_k,
        rerank=bool(payload.get("rerank", True)),
        rerank_candidates=max(top_k, min(20, top_k * 2)),
        max_steps=min(8, max(1, int(payload.get("maxSteps", 5)))),
        timeout_seconds=min(60.0, max(1.0, float(payload.get("timeoutSeconds", 15)))),
    ).validate()


def answer_question(payload, dataset, chunks):
    question, config = validate_request(payload)
    started = time.perf_counter()
    search_started = time.perf_counter()
    hits = _retrieve({"question": question}, chunks, config)
    search_seconds = time.perf_counter() - search_started
    best_score = (
        (
            hits[0].rerank_score
            if hits and hits[0].rerank_score is not None
            else hits[0].score
        )
        if hits
        else 0.0
    )
    if not hits or best_score < 0.08:
        return {
            "status": "no_evidence",
            "answer": "資料内では確認できません。",
            "citations": [],
            "unsupportedClaims": [],
            "mode": config.mode,
            "retrieval": config.retrieval,
            "datasetVersion": dataset["version"],
            "timings": {
                "searchSeconds": search_seconds,
                "answerSeconds": 0.0,
                "verificationSeconds": 0.0,
                "totalSeconds": time.perf_counter() - started,
            },
        }

    answer_started = time.perf_counter()
    # Offline mode deliberately returns extractive evidence instead of
    # pretending that a language model generated a novel mathematical answer.
    selected = hits[: min(2, len(hits))]
    raw_answer = "\n\n".join(
        f"{hit.chunk.text} {format_citation(hit.chunk)}" for hit in selected
    )
    answer_seconds = time.perf_counter() - answer_started
    verify_started = time.perf_counter()
    verification = validate_citations(raw_answer, hits)
    verification_seconds = time.perf_counter() - verify_started
    if not verification["valid"]:
        raise RuntimeError("citation validation failed")

    citations = []
    display_answer = raw_answer
    for number, hit in enumerate(selected, start=1):
        marker = format_citation(hit.chunk)
        display_answer = display_answer.replace(marker, f"[{number}]", 1)
        citations.append(
            {
                "number": number,
                "documentId": hit.chunk.document_id,
                "documentTitle": DOCUMENT_TITLES.get(
                    hit.chunk.document_id, hit.chunk.document_id
                ),
                "documentVersion": hit.chunk.document_version,
                "pageNumber": hit.chunk.page_number,
                "chunkId": hit.chunk.chunk_id,
                "text": hit.chunk.text,
                "score": hit.rerank_score
                if hit.rerank_score is not None
                else hit.score,
                "sourceUrl": None,
                "retrievalMethod": config.retrieval
                + ("+rerank" if config.rerank else ""),
                "ocrDerived": hit.chunk.ocr_derived,
            }
        )

    total_seconds = time.perf_counter() - started
    return {
        "status": "success",
        "answer": display_answer,
        "citations": citations,
        "unsupportedClaims": [],
        "mode": config.mode,
        "roles": ["single"]
        if config.mode == "single"
        else ["coordinator", "retriever", "solver", "verifier", "tutor"],
        "retrieval": config.retrieval,
        "datasetVersion": dataset["version"],
        "model": config.model,
        "modelCalls": 0,
        "usage": {
            "inputTokens": 0,
            "outputTokens": 0,
            "costUsd": 0.0,
            "costScope": "external-model-api-only",
        },
        "timings": {
            "searchSeconds": search_seconds,
            "answerSeconds": answer_seconds,
            "verificationSeconds": verification_seconds,
            "totalSeconds": total_seconds,
        },
        "limits": {
            key: value
            for key, value in asdict(config).items()
            if key
            in {
                "max_steps",
                "max_tokens",
                "timeout_seconds",
                "retries",
                "concurrency",
                "cost_limit_usd",
            }
        },
        "notice": "オフライン抽出回答です。数学的な正しさや完全性を保証しません。",
    }


def create_handler(dataset, chunks):
    class Handler(BaseHTTPRequestHandler):
        server_version = "MathResearchAPI/1"

        def _json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if urlparse(self.path).path == "/health":
                self._json(
                    200,
                    {
                        "status": "ok",
                        "datasetVersion": dataset["version"],
                        "externalModelCalls": False,
                    },
                )
            else:
                self._json(
                    404,
                    {"error": {"code": "not_found", "message": "Endpoint not found"}},
                )

        def do_POST(self):
            if urlparse(self.path).path != "/v1/query":
                self._json(
                    404,
                    {"error": {"code": "not_found", "message": "Endpoint not found"}},
                )
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY_BYTES:
                    raise ValueError("request body size is invalid")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self._json(200, answer_question(payload, dataset, chunks))
            except (ValueError, json.JSONDecodeError) as error:
                self._json(
                    400, {"error": {"code": "invalid_request", "message": str(error)}}
                )
            except Exception:
                self._json(
                    500,
                    {
                        "error": {
                            "code": "internal_error",
                            "message": "検索処理に失敗しました。",
                        }
                    },
                )

        def log_message(self, pattern, *args):
            # Never log request bodies or prompts.
            print(f"{self.address_string()} - {pattern % args}")

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    dataset, chunks = load_corpus()
    server = ThreadingHTTPServer(
        (args.host, args.port), create_handler(dataset, chunks)
    )
    print(f"Research API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nResearch API stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

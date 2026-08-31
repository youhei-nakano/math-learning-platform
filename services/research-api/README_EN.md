# Reproducible Mathematics Learning Research Platform

This repository combines the existing guarded mathematics sandbox with an
offline-first research platform for versioned multi-PDF ingestion, keyword/local
vector/hybrid retrieval, optional reranking, bounded single/multi orchestration,
citation validation, and resumable evaluation. `my-app` remains the React
learning-map client. Its grounded-question UI reaches this repository through a
same-origin BFF; node notes are never included in that request.

## Main empirical result

The production live comparison is complete. Using the frozen
`gpt-5.4-mini-2026-03-17` snapshot, the experiment compared a single answer
call with a Coordinator–Retriever–Solver–Verifier–Tutor pipeline on 27 cases
and five trials (135 paired observations). Both conditions achieved 81.5%
answer accuracy. The multi-agent pipeline cost 5.8x more and had 8.4x higher
median latency; its wins/ties/losses were 17/101/17. The single-call condition
therefore remains the production default for this task and evidence set.

Read the [technical report](../../docs/technical-report.md), the
[live-results summary](evaluation/LIVE_RESULTS.md), and the
[frozen protocol](docs/live_evaluation.md). Blind human audit remains pending.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python evaluation/datasets/demo-v1/generate_fixtures.py
python -m unittest discover -s tests -v
python research_api.py
python evaluation/run_research.py --config evaluation/configs/single-hybrid-rerank.json --output evaluation/runs/single.jsonl
python evaluation/report_research.py evaluation/runs/*.jsonl --csv evaluation/results.csv --markdown evaluation/RESULTS.md
```

The local API listens on `127.0.0.1:8765`, exposes only the checked-in CC0 demo
corpus, and returns extractive evidence without calling an external model.

Set `OPENAI_API_KEY` only for explicitly approved legacy/live experiments.
Offline research commands do not require it. Config fields select single/multi,
model, limits, retrieval, top-k, reranking, OCR/VLM, retries, concurrency, and
cost cap. OCR/VLM interfaces exist but live adapters are not implemented.

See `docs/research_architecture.md`, `docs/reproducibility.md`,
`docs/security_privacy.md`, and `docs/user_study_protocol.md`. The demo fixtures
are original CC0 assets. User PDFs, indexes, secrets, and participant data must
not be committed. No public deployment or user study has been conducted.

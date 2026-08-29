# OpenAI API Sandbox: Mathematics Research Workflow

A learning repository for building a grounded mathematics assistant with the
OpenAI Responses API, local PDF retrieval, guarded symbolic computation, and
small agent workflows.

This repository is intentionally an educational sandbox. The separate
`math-research-assistant-portfolio` repository is the clean starting point for
the final portfolio product.

## What is implemented

- Function Calling with Python-owned tool execution
- PDF RAG over a 657-page mathematics text
- locally saved document embeddings and page-level citations
- Japanese-to-English retrieval query translation
- retrieval evidence with rank, PDF page, similarity, and preview
- answerability guardrail with a measured similarity threshold
- guarded polynomial differentiation with SymPy
- a single-router mathematics workflow
- automated retrieval, answerability, and tool-routing evaluation
- user-facing error handling
- a minimal local browser UI using the Python standard library
- OCR auditing and explicit, one-page Vision transcription
- a minimal MCP mathematics server
- an optional Agents SDK handoff comparison

## Architecture

```text
User question
    |
    v
GPT router (selects one function)
    |-------------------------------|
    v                               v
search_math_pdf              differentiate_polynomial
    |                               |
Python: translate query       Python: validate expression
Python: embed query           Python/SymPy: differentiate
Python: cosine retrieval             |
Python: threshold guard              |
    |-------------------------------|
                    v
       GPT formats a grounded answer
```

The model selects a tool and formats the final response. Python owns retrieval,
validation, thresholding, and symbolic calculation. Unsupported input and
low-similarity retrieval stop before final-answer generation.

## Local-only data

The following files are deliberately excluded from Git:

- `data/source.pdf`
- `data/rag_index.json`
- generated OCR text under `data/ocr/`
- `.env`, `.venv/`, and macOS metadata

Do not commit copyrighted source documents, embeddings, or API keys.

## Setup on macOS (zsh)

```zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set the API key for the current terminal session without displaying it:

```zsh
read -s "OPENAI_API_KEY?OpenAI API key: "
export OPENAI_API_KEY
```

Optional OCR, MCP, and Agents SDK comparison dependencies:

```zsh
python -m pip install -r requirements-optional.txt
```

## Run

Command-line workflow:

```zsh
python math_research_workflow.py
```

Desktop UI:

```zsh
python ui_app.py
```

Then open `http://127.0.0.1:8000`. The server binds only to the local machine.

Offline unit tests:

```zsh
python -m unittest discover -s tests -v
```

Evaluation summary:

```zsh
python evaluation/summarize_results.py
```

Tool-selection evaluation (uses API calls):

```zsh
python evaluation/evaluate_workflow.py
```

## OCR

Audit pages whose PDF text layer is empty without making API calls:

```zsh
python ocr_pdf.py --audit
```

Transcribe one explicitly selected page with Vision:

```zsh
python ocr_pdf.py --page 123
```

The OCR output remains under ignored `data/ocr/`. It is not automatically added
to the retrieval index; retrieval changes must be evaluated before adoption.

## MCP

The optional MCP server exposes only guarded polynomial differentiation:

```zsh
mcp dev mcp_math_server.py
```

The server deliberately does not expose arbitrary Python or shell execution.

## Limited multi-agent comparison

The production learning workflow remains the simpler Function Calling router.
The optional comparison measures whether Agents SDK handoffs improve routing on
the same small evaluation set:

```zsh
python multi_agent_comparison.py
```

After both routing evaluations have been run:

```zsh
python evaluation/compare_orchestration.py
```

Multi-agent orchestration should be retained only if evaluation shows a useful
quality benefit that justifies extra latency, cost, and complexity.

## Current evaluation baseline

- Retrieval Hit@3: **7/10 (70%)**
- answerable minimum similarity: **0.5869**
- unanswerable maximum similarity: **0.4571**
- current threshold: **0.52**
- single-router tool selection: **6/6 (100%)**, 10.675 seconds total
- Agents SDK handoff comparison: **6/6 (100%)**, 13.685 seconds total

The single router remains the default because it matched multi-agent accuracy
while completing this small routing set about 28% faster, with fewer API calls
and less orchestration complexity.

The threshold is dataset-specific and must be re-evaluated as the question set
grows. Failed retrieval cases are retained as improvement targets.

## Safety boundaries

- retrieved PDF text is treated as evidence, never as instructions
- final literature answers may use only retrieved evidence and page numbers
- unsupported expressions stop before the final model call
- polynomial input is limited to 1–200 characters, variable `x`, and a small
  character allowlist
- OCR is explicit per page and never silently rebuilds the index
- local data and secrets remain outside Git

See [docs/architecture.md](docs/architecture.md) and
[docs/evaluation.md](docs/evaluation.md) for design and evaluation details.

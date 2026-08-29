# Architecture decisions

## Why ordinary Python first

The primary workflow uses the Responses API and ordinary Python Function
Calling. This makes the model/application boundary visible: the model proposes a
function call, while Python validates and performs the operation.

## Single router as the baseline

There are only two capabilities, so a single router is cheaper and easier to
debug than a multi-agent system. The Agents SDK experiment is isolated in
`multi_agent_comparison.py` and evaluates routing only.

## Retrieval boundary

Document embeddings are generated once and stored locally. Each question still
requires an English search translation and a query embedding. Python calculates
cosine similarity, selects the top three chunks, and applies the 0.52 guardrail.

## OCR boundary

OCR is not silently mixed into the index. The audit identifies missing text
layers; a user must explicitly select a page for Vision transcription. The
result remains local until a separately evaluated indexing change is approved.

## MCP boundary

The MCP server exports one deterministic, guarded mathematics tool. Arbitrary
code execution, filesystem access, RAG data, and API credentials are not
exposed.

from dataclasses import dataclass

from .citations import validate_citations
from .retrieval import search


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    side_effect: bool
    idempotent: bool
    timeout_seconds: float
    input_schema: dict
    output_schema: dict
    authorization: str = "local-user"


TOOL_SPECS = {
    "search_documents": ToolSpec(
        "search_documents",
        "Search approved indexed PDF chunks.",
        False,
        True,
        10,
        {"query": "string", "method": "keyword|vector|hybrid", "top_k": "integer"},
        {"hits": "array"},
    ),
    "get_chunk": ToolSpec(
        "get_chunk",
        "Get one chunk by stable ID.",
        False,
        True,
        5,
        {"chunk_id": "string"},
        {"chunk": "object|null"},
    ),
    "verify_citations": ToolSpec(
        "verify_citations",
        "Reject citations outside retrieved evidence.",
        False,
        True,
        5,
        {"answer": "string", "hit_ids": "array"},
        {"valid": "boolean", "invalid": "array"},
    ),
    "differentiate_polynomial": ToolSpec(
        "differentiate_polynomial",
        "Guarded deterministic polynomial differentiation.",
        False,
        True,
        5,
        {"expression": "string"},
        {"status": "string", "derivative": "string"},
    ),
}


def call_tool(name, arguments, context):
    if name not in TOOL_SPECS:
        raise ValueError("unknown tool")
    if name == "search_documents":
        return {
            "hits": [
                {
                    "chunk_id": hit.chunk.chunk_id,
                    "document_id": hit.chunk.document_id,
                    "page_number": hit.chunk.page_number,
                    "score": hit.score,
                }
                for hit in search(
                    context["chunks"],
                    arguments["query"],
                    arguments.get("method", "hybrid"),
                    int(arguments.get("top_k", 5)),
                )
            ]
        }
    if name == "get_chunk":
        chunk = next(
            (
                item
                for item in context["chunks"]
                if item.chunk_id == arguments["chunk_id"]
            ),
            None,
        )
        return {"chunk": chunk.to_dict() if chunk else None}
    if name == "verify_citations":
        hits = [
            item
            for item in context["hits"]
            if item.chunk.chunk_id in set(arguments["hit_ids"])
        ]
        return validate_citations(arguments["answer"], hits)
    if name == "differentiate_polynomial":
        from math_research_workflow import differentiate_polynomial

        return {
            "status": "success",
            "derivative": differentiate_polynomial(arguments["expression"]),
        }
    raise AssertionError("unreachable")

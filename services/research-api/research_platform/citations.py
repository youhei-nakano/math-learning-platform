import re

CITATION_RE = re.compile(r"\[([^\]]+) p\. (\d+), chunk ([^\]]+)\]")


def format_citation(chunk):
    return f"[{chunk.document_id} p. {chunk.page_number}, chunk {chunk.chunk_id}]"


def validate_citations(answer, hits):
    allowed = {
        (hit.chunk.document_id, hit.chunk.page_number, hit.chunk.chunk_id)
        for hit in hits
    }
    found = {
        (doc, int(page), chunk) for doc, page, chunk in CITATION_RE.findall(answer)
    }
    return {
        "valid": found.issubset(allowed),
        "found": sorted(found),
        "invalid": sorted(found - allowed),
        "citation_count": len(found),
    }

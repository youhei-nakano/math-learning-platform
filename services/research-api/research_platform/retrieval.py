import math
import re
from collections import Counter
from dataclasses import replace
from hashlib import sha256

from .models import SearchHit

TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u3040-\u30ff\u3400-\u9fff]")


def tokens(text):
    return TOKEN_RE.findall(text.lower())


def local_vector(text, dimensions=128):
    vector = [0.0] * dimensions
    for token in tokens(text):
        vector[int(sha256(token.encode()).hexdigest()[:8], 16) % dimensions] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def keyword_score(query, text):
    wanted, found = Counter(tokens(query)), Counter(tokens(text))
    return sum(min(count, found[token]) for token, count in wanted.items()) / max(
        sum(wanted.values()), 1
    )


def vector_score(query, text):
    left, right = local_vector(query), local_vector(text)
    return sum(a * b for a, b in zip(left, right))


def search(chunks, query, method="hybrid", top_k=5, candidates=None):
    if method == "none":
        return []
    hits = []
    for chunk in chunks:
        keyword, vector = (
            keyword_score(query, chunk.text),
            vector_score(query, chunk.text),
        )
        score = (
            keyword
            if method == "keyword"
            else vector
            if method == "vector"
            else 0.55 * keyword + 0.45 * vector
        )
        hits.append(SearchHit(chunk, score, keyword, vector))
    return sorted(hits, key=lambda item: (-item.score, item.chunk.chunk_id))[
        : candidates or top_k
    ]


def rerank(hits, query, top_k=5):
    query_terms = set(tokens(query))
    output = []
    for hit in hits:
        coverage = len(query_terms.intersection(tokens(hit.chunk.text))) / max(
            len(query_terms), 1
        )
        output.append(replace(hit, rerank_score=0.7 * hit.score + 0.3 * coverage))
    return sorted(
        output, key=lambda item: (-(item.rerank_score or 0), item.chunk.chunk_id)
    )[:top_k]

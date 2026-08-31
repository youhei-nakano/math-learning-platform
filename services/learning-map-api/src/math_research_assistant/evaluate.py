"""Offline comparison of an AI graph JSON file with the reviewed demo baseline."""

import argparse
import json
import time
from pathlib import Path

BASELINE_NODES = {
    "matrix-product",
    "invertible",
    "vector-space",
    "subspace",
    "independence",
    "basis-dimension",
    "linear-map",
    "representation",
    "basis-change",
    "eigenvalue-vector",
    "eigenspace",
    "diagonalization",
    "diagonalizable-condition",
    "inner-product",
    "orthogonality",
    "orthonormal-basis",
    "gram-schmidt",
    "orthogonal-matrix",
    "symmetric-matrix",
    "real-eigenvalues",
    "orthogonal-eigenvectors",
    "orthogonal-diagonalization",
}


def evaluate(graph: dict, page_count: int = 432) -> dict:
    started = time.perf_counter()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    ids = {node.get("id") for node in nodes}
    matched = ids & BASELINE_NODES
    invalid_pages = sum(
        page < 1 or page > page_count
        for node in nodes
        for page in node.get("sourcePages", [])
    )
    adjacency = {node_id: [] for node_id in ids}
    edge_matches = 0
    for edge in edges:
        source, target = edge.get("sourceId"), edge.get("targetId")
        if source in adjacency and target in adjacency:
            adjacency[source].append(target)
        if source in BASELINE_NODES and target in BASELINE_NODES:
            edge_matches += 1
    visiting, visited = set(), set()

    def cycle(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        found = any(cycle(target) for target in adjacency[node_id])
        visiting.remove(node_id)
        visited.add(node_id)
        return found

    cycles = int(any(cycle(node_id) for node_id in ids))
    usage = graph.get("usage")
    return {
        "baselineNodeRecall": round(len(matched) / len(BASELINE_NODES), 3),
        "extraNodeCount": len(ids - BASELINE_NODES),
        "missingNodeCount": len(BASELINE_NODES - ids),
        "dependencyMatchCount": edge_matches,
        "invalidSourcePageCount": invalid_pages,
        "cycleCount": cycles,
        "processingSeconds": round(time.perf_counter() - started, 6),
        "apiUsage": usage,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(json.loads(args.graph_json.read_text(encoding="utf-8")))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()

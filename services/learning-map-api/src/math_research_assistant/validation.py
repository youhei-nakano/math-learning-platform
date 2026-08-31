from collections import Counter, defaultdict

from .schemas import GeneratedGraph


class GraphValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def reject_unsupplied_evidence(
    graph: GeneratedGraph, allowed_pages: set[int], page_count: int
) -> list[str]:
    """Remove hallucinated citations without treating them as PDF evidence.

    A non-goal node that loses every supplied citation becomes an excluded external
    prerequisite suggestion. A goal without supplied evidence remains a hard error,
    because silently inventing or replacing its source would misrepresent the PDF.
    """
    warnings: list[str] = []
    errors: list[str] = []
    for node in graph.nodes:
        rejected = sorted(
            {
                page
                for page in [
                    *node.sourcePages,
                    *(item.page for item in node.evidence if item.page),
                ]
                if 1 <= page <= page_count and page not in allowed_pages
            }
        )
        if not rejected:
            continue
        node.sourcePages = [page for page in node.sourcePages if page in allowed_pages]
        node.evidence = [
            item
            for item in node.evidence
            if item.page is None or item.page in allowed_pages
        ]
        warnings.append(
            f"未送信ページの根拠を除外: node {node.id} p."
            + ", p.".join(map(str, rejected))
        )
        if node.sourceType == "pdf-evidence" and not node.sourcePages:
            if node.type == "goal":
                errors.append(f"goal source page was not supplied: {node.id}")
                continue
            node.sourceType = "external-prerequisite-suggestion"
            node.included = False
            node.importance = "supporting"
            node.confidence = "low"
            node.sourceSections = []
            node.evidence = []
            warnings.append(
                f"PDF内根拠が残らないためPDF外前提候補（未採用）へ変更: {node.id}"
            )
    for edge in graph.edges:
        rejected = sorted(
            page
            for page in edge.evidencePages
            if 1 <= page <= page_count and page not in allowed_pages
        )
        if not rejected:
            continue
        edge.evidencePages = [
            page for page in edge.evidencePages if page in allowed_pages
        ]
        edge.confidence = "low"
        warnings.append(
            f"未送信ページの根拠を除外: edge {edge.id} p."
            + ", p.".join(map(str, rejected))
        )
    if errors:
        raise GraphValidationError(errors)
    graph.warnings.extend(
        warning for warning in warnings if warning not in graph.warnings
    )
    return warnings


def downgrade_unreachable_required_nodes(graph: GeneratedGraph) -> list[str]:
    """Keep uncertain nodes visible without inventing missing dependency edges."""
    goals = [node for node in graph.nodes if node.type == "goal"]
    if len(goals) != 1:
        return []
    reverse: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        reverse[edge.targetId].append(edge.sourceId)
    reachable = {goals[0].id}
    stack = [goals[0].id]
    while stack:
        for source in reverse[stack.pop()]:
            if source not in reachable:
                reachable.add(source)
                stack.append(source)
    downgraded = []
    for node in graph.nodes:
        if node.importance == "required" and node.id not in reachable:
            node.importance = "recommended"
            node.confidence = "low"
            downgraded.append(node.id)
    if downgraded:
        graph.warnings.append(
            "目標への依存経路が生成されなかったため、必須から推奨へ変更: "
            + ", ".join(downgraded)
        )
    return downgraded


def validate_graph(
    graph: GeneratedGraph,
    page_count: int,
    max_nodes: int = 30,
    allowed_pages: set[int] | None = None,
) -> None:
    errors: list[str] = []
    node_counts = Counter(node.id for node in graph.nodes)
    edge_counts = Counter(edge.id for edge in graph.edges)
    errors += [
        f"duplicate node id: {key}" for key, count in node_counts.items() if count > 1
    ]
    errors += [
        f"duplicate edge id: {key}" for key, count in edge_counts.items() if count > 1
    ]
    if len(graph.nodes) > max_nodes:
        errors.append("node limit exceeded")
    goals = [node for node in graph.nodes if node.type == "goal"]
    if len(goals) != 1:
        errors.append("graph must contain exactly one goal")
    ids = set(node_counts)
    adjacency: dict[str, list[str]] = defaultdict(list)
    for node in graph.nodes:
        if node.sourceType == "pdf-evidence" and not node.sourcePages:
            errors.append(f"missing source page: {node.id}")
        if (
            node.sourceType == "external-prerequisite-suggestion"
            and node.importance == "required"
            and node.included
        ):
            errors.append(f"external prerequisite automatically required: {node.id}")
        for page in [
            *node.sourcePages,
            *(item.page for item in node.evidence if item.page),
        ]:
            if page < 1 or page > page_count:
                errors.append(f"source page out of range: {node.id}:{page}")
            elif allowed_pages is not None and page not in allowed_pages:
                errors.append(f"source page was not supplied: {node.id}:{page}")
    for edge in graph.edges:
        if edge.sourceId not in ids or edge.targetId not in ids:
            errors.append(f"unknown node reference: {edge.id}")
            continue
        if edge.sourceId == edge.targetId:
            errors.append(f"self loop: {edge.id}")
        if (
            edge.confirmationStatus != "unconfirmed"
            or edge.relationKind == "user-confirmed"
        ):
            errors.append(f"AI edge was automatically confirmed: {edge.id}")
        for page in edge.evidencePages:
            if page < 1 or page > page_count:
                errors.append(f"edge source page out of range: {edge.id}:{page}")
            elif allowed_pages is not None and page not in allowed_pages:
                errors.append(f"edge source page was not supplied: {edge.id}:{page}")
        adjacency[edge.sourceId].append(edge.targetId)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        if any(visit(next_id) for next_id in adjacency[node_id]):
            return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    if any(visit(node_id) for node_id in ids):
        errors.append("dependency cycle detected")
    if goals:
        reverse: dict[str, list[str]] = defaultdict(list)
        for source, targets in adjacency.items():
            for target in targets:
                reverse[target].append(source)
        reachable = {goals[0].id}
        stack = [goals[0].id]
        while stack:
            stack.extend(
                item
                for item in reverse[stack.pop()]
                if item not in reachable and not reachable.add(item)
            )
        for node in graph.nodes:
            if node.importance == "required" and node.id not in reachable:
                errors.append(f"required node cannot reach goal: {node.id}")
    if errors:
        raise GraphValidationError(sorted(set(errors)))

from fastapi.testclient import TestClient

from math_research_assistant.app import app, get_ai_service
from math_research_assistant.openai_service import OpenAIStructuredClient
from math_research_assistant.schemas import (
    GeneratedGraph,
    ReviewResponse,
    SelectionResponse,
)


def node(node_id="basis", node_type="definition", pages=None, **updates):
    value = {
        "id": node_id,
        "title": node_id,
        "canonicalName": node_id,
        "aliases": [],
        "type": node_type,
        "reason": "needed",
        "relationToGoal": "supports goal",
        "understandingLevel": "explain",
        "completionCriteria": "can explain",
        "importance": "required",
        "sourcePages": pages or [2],
        "sourceSections": ["S"],
        "evidence": [
            {
                "page": (pages or [2])[0],
                "section": "S",
                "description": "definition appears",
            }
        ],
        "confidence": "high",
        "confirmationStatus": "unconfirmed",
        "included": True,
        "sourceType": "pdf-evidence",
    }
    value.update(updates)
    return value


def graph(**updates):
    value = {
        "nodes": [node(), node("goal", "goal", [3])],
        "edges": [
            {
                "id": "basis-goal",
                "sourceId": "basis",
                "targetId": "goal",
                "type": "definition-required",
                "rationale": "needed",
                "evidencePages": [2, 3],
                "confidence": "high",
                "confirmationStatus": "unconfirmed",
                "relationKind": "ai-concept-dependency",
            }
        ],
        "warnings": [],
    }
    value.update(updates)
    return value


class FakeService:
    def __init__(self, generated=None):
        self.generated = generated or graph()

    def select_sections(self, _payload):
        return SelectionResponse.model_validate(
            {
                "sections": [
                    {
                        "outlineId": "s1",
                        "title": "Section",
                        "startPage": 2,
                        "endPage": 3,
                        "rationale": "relevant",
                        "confidence": "high",
                    }
                ],
                "warnings": [],
            }
        )

    def generate(self, _payload):
        return GeneratedGraph.model_validate(self.generated)

    def review(self, _payload):
        return ReviewResponse.model_validate(
            {
                "issues": [
                    {
                        "id": "i1",
                        "targetKind": "edge",
                        "targetId": "basis-goal",
                        "type": "source-mismatch",
                        "description": "check evidence",
                        "check": "read p.2",
                        "severity": "medium",
                        "resolved": False,
                    }
                ],
                "summary": "one issue",
                "warnings": [],
            }
        )


def client(service=None):
    app.dependency_overrides[get_ai_service] = lambda: service or FakeService()
    return TestClient(app)


SELECTION = {
    "title": "Book",
    "author": "A",
    "pageCount": 10,
    "outline": [
        {"id": "s1", "title": "Section", "level": 0, "pdfPage": 2, "parentId": None}
    ],
    "goal": "Goal",
    "understandingLevel": "explain",
    "maxSections": 10,
    "maxPages": 50,
}
GENERATE = {
    "title": "Book",
    "author": "A",
    "pageCount": 10,
    "goal": "Goal",
    "understandingLevel": "explain",
    "sections": [
        {
            "outlineId": "s1",
            "title": "Section",
            "startPage": 2,
            "endPage": 3,
            "rationale": "relevant",
            "confidence": "high",
        }
    ],
    "pages": [
        {"page": 2, "text": "a sufficiently long extracted page text"},
        {"page": 3, "text": "another sufficiently long page text"},
    ],
    "maxNodes": 30,
    "maxPages": 50,
}


def test_health_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["aiAvailable"] is False


def test_selection_generation_and_review_schemas():
    api = client()
    assert (
        api.post("/api/learning-map/select-sections", json=SELECTION).status_code == 200
    )
    generated = api.post("/api/learning-map/generate", json=GENERATE)
    assert generated.status_code == 200
    reviewed = api.post(
        "/api/learning-map/review",
        json={
            "pageCount": 10,
            "goal": "Goal",
            "pages": GENERATE["pages"],
            "graph": generated.json(),
        },
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["issues"][0]["resolved"] is False


def test_rejects_invalid_page_unknown_reference_cycle_and_limits():
    bad_pages = graph(nodes=[node(pages=[11]), node("goal", "goal", [3])])
    assert (
        client(FakeService(bad_pages))
        .post("/api/learning-map/generate", json=GENERATE)
        .status_code
        == 422
    )
    unsupplied_page = graph(
        nodes=[node(pages=[4]), node("goal", "goal", [3])],
        edges=[{**graph()["edges"][0], "evidencePages": [2, 4]}],
    )
    response = client(FakeService(unsupplied_page)).post(
        "/api/learning-map/generate", json=GENERATE
    )
    assert response.status_code == 200
    repaired = response.json()
    assert repaired["nodes"][0]["sourceType"] == "external-prerequisite-suggestion"
    assert repaired["nodes"][0]["included"] is False
    assert repaired["nodes"][0]["sourcePages"] == []
    assert repaired["edges"][0]["evidencePages"] == [2]
    assert "未送信ページの根拠を除外" in " / ".join(repaired["warnings"])
    bad_ref = graph(edges=[{**graph()["edges"][0], "sourceId": "missing"}])
    assert (
        client(FakeService(bad_ref))
        .post("/api/learning-map/generate", json=GENERATE)
        .status_code
        == 422
    )
    cycle = graph(
        edges=[
            graph()["edges"][0],
            {
                **graph()["edges"][0],
                "id": "back",
                "sourceId": "goal",
                "targetId": "basis",
            },
        ]
    )
    assert (
        client(FakeService(cycle))
        .post("/api/learning-map/generate", json=GENERATE)
        .status_code
        == 422
    )
    too_many = graph(
        nodes=[node(f"n{i}") for i in range(31)] + [node("goal", "goal", [3])]
    )
    assert (
        client(FakeService(too_many))
        .post("/api/learning-map/generate", json=GENERATE)
        .status_code
        == 422
    )


def test_external_prerequisite_must_not_be_auto_required():
    external = node(
        "external",
        pages=[],
        sourceType="external-prerequisite-suggestion",
        importance="required",
        included=True,
        evidence=[{"page": None, "section": None, "description": "not in PDF"}],
    )
    invalid = graph(
        nodes=[external, node("goal", "goal", [3])],
        edges=[{**graph()["edges"][0], "sourceId": "external"}],
    )
    response = client(FakeService(invalid)).post(
        "/api/learning-map/generate", json=GENERATE
    )
    assert response.status_code == 422
    assert "external prerequisite" in str(response.json())


class BrokenService(FakeService):
    def generate(self, _payload):
        raise RuntimeError("upstream failed")


class MismatchedOutlineService(FakeService):
    def select_sections(self, _payload):
        return SelectionResponse.model_validate(
            {
                "sections": [
                    {
                        "outlineId": "hallucinated-id",
                        "title": "Section",
                        "startPage": 9,
                        "endPage": 9,
                        "rationale": "relevant",
                        "confidence": "medium",
                    }
                ],
                "warnings": [],
            }
        )


def test_api_error_and_request_page_limit():
    assert (
        client(BrokenService())
        .post("/api/learning-map/generate", json=GENERATE)
        .status_code
        == 503
    )
    request = {
        **GENERATE,
        "pages": [
            {"page": i, "text": "a sufficiently long extracted page text"}
            for i in range(1, 52)
        ],
    }
    assert client().post("/api/learning-map/generate", json=request).status_code == 422


def test_unknown_outline_id_is_repaired_only_by_unique_title():
    response = client(MismatchedOutlineService()).post(
        "/api/learning-map/select-sections", json=SELECTION
    )
    assert response.status_code == 200
    assert response.json()["sections"][0]["outlineId"] == "s1"
    assert "補正" in response.json()["warnings"][0]


def test_unreachable_required_node_is_downgraded_without_inventing_edge():
    disconnected = node("detached")
    candidate = graph(nodes=[disconnected, node("goal", "goal", [3])], edges=[])
    response = client(FakeService(candidate)).post(
        "/api/learning-map/generate", json=GENERATE
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["nodes"][0]["importance"] == "recommended"
    assert payload["nodes"][0]["confidence"] == "low"
    assert payload["edges"] == []
    assert "必須から推奨" in payload["warnings"][0]


def test_empty_graph_and_missing_api_key(monkeypatch):
    empty = graph(nodes=[], edges=[])
    assert (
        client(FakeService(empty))
        .post("/api/learning-map/generate", json=GENERATE)
        .status_code
        == 422
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    missing = OpenAIStructuredClient()
    try:
        missing.create(schema=GeneratedGraph, instructions="test", payload={})
    except RuntimeError as error:
        assert "OPENAI_API_KEY" in str(error)
    else:
        raise AssertionError("missing API key must fail safely")

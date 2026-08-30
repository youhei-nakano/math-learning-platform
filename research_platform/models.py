from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Chunk:
    document_id: str
    document_version: str
    page_number: int
    chunk_id: str
    text: str
    section: str = ""
    ocr_derived: bool = False
    figure_relation: str | None = None
    bbox: list[float] | None = None

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float
    keyword_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float | None = None


@dataclass
class RunResult:
    case_id: str
    experiment_id: str
    status: str
    answer: str
    citations: list[dict]
    latency_seconds: float
    tool_calls: int
    steps: int
    usage: dict = field(
        default_factory=lambda: {
            "input_tokens": None,
            "output_tokens": None,
            "cost_usd": 0.0,
        }
    )
    error: str | None = None
    trace: list[dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

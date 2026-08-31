import json
from dataclasses import asdict, dataclass
from hashlib import sha256


@dataclass(frozen=True)
class ExperimentConfig:
    mode: str = "single"
    model: str = "offline-extractive-v1"
    temperature: float = 0.0
    max_steps: int = 5
    max_tokens: int = 2_000
    retrieval: str = "hybrid"
    top_k: int = 5
    rerank: bool = True
    rerank_candidates: int = 10
    ocr: bool = False
    vlm: bool = False
    timeout_seconds: float = 30.0
    retries: int = 1
    concurrency: int = 1
    cost_limit_usd: float = 0.25
    prompt_version: str = "research-v1"

    def validate(self):
        if self.mode not in {"single", "multi"}:
            raise ValueError("mode must be single or multi")
        if self.retrieval not in {"none", "keyword", "vector", "hybrid"}:
            raise ValueError("unsupported retrieval mode")
        if not 1 <= self.max_steps <= 20 or not 1 <= self.top_k <= 50:
            raise ValueError("step/top-k limit is out of range")
        if self.rerank_candidates < self.top_k:
            raise ValueError("rerank_candidates must be >= top_k")
        if self.cost_limit_usd < 0:
            raise ValueError("cost limit cannot be negative")
        return self

    def experiment_id(self, dataset_version, code_version="dirty"):
        payload = json.dumps(
            {"config": asdict(self), "dataset": dataset_version, "code": code_version},
            sort_keys=True,
        )
        return sha256(payload.encode()).hexdigest()[:16]

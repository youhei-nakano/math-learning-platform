from dataclasses import dataclass


@dataclass(frozen=True)
class ModalityResult:
    status: str
    text: str = ""
    confidence: float | None = None
    latency_seconds: float = 0.0
    cost_usd: float = 0.0
    provenance: str = "pdf-text-layer"
    error: str | None = None


class DisabledOcrAdapter:
    def extract(self, _path, _page_number):
        raise RuntimeError("OCR is disabled; enable and configure an explicit adapter")


class DisabledVlmAdapter:
    def describe(self, _image, _purpose):
        return ModalityResult(
            "not_run", provenance="vlm-inference", error="VLM is disabled"
        )

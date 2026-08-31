import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config/openai-generation.json"
_CONFIG = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))

GENERATION_MODEL = _CONFIG["model_id"]
GENERATION_MODEL_DISPLAY = _CONFIG["display_name"]


def require_generation_model(model):
    if model != GENERATION_MODEL:
        raise ValueError(
            f"production generation model must be {GENERATION_MODEL}, got {model}"
        )
    return model

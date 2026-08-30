"""Reproducible, offline-first research platform for the math learning assistant."""

from .config import ExperimentConfig
from .orchestration import run_case

__all__ = ["ExperimentConfig", "run_case"]

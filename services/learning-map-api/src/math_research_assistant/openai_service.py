import json
import os
import re
from typing import Protocol, TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel

from .schemas import GeneratedGraph, ReviewResponse, SelectionResponse

T = TypeVar("T", bound=BaseModel)


def safe_connection_reason(error: BaseException) -> str:
    """Return a short diagnostic without exposing authorization headers or keys."""
    chain = []
    current: BaseException | None = error
    while current is not None and len(chain) < 5:
        message = str(current)
        message = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-[REDACTED]", message)
        message = re.sub(
            r"(?i)(authorization[^:]*:\s*)([^,}\]]+)", r"\1[REDACTED]", message
        )
        chain.append(f"{type(current).__name__}: {message[:240]}")
        current = current.__cause__ or current.__context__
    return " <- ".join(chain)


class StructuredClient(Protocol):
    def create(self, *, schema: type[T], instructions: str, payload: dict) -> T: ...


class OpenAIStructuredClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")

    @property
    def available(self) -> bool:
        return self.configuration_error is None

    @property
    def configuration_error(self) -> str | None:
        if not self.api_key:
            return "OPENAI_API_KEYが設定されていません。"
        if self.api_key != self.api_key.strip():
            return "OPENAI_API_KEYの先頭または末尾に空白・改行があります。"
        if not self.api_key.startswith("sk-"):
            return (
                "OPENAI_API_KEYの形式が正しくありません（sk-で始まる必要があります）。"
            )
        if not self.api_key.isascii():
            return "OPENAI_API_KEYに全角文字またはASCII以外の文字が含まれています。"
        return None

    def create(self, *, schema: type[T], instructions: str, payload: dict) -> T:
        if self.configuration_error:
            raise RuntimeError(self.configuration_error)
        # Large strict schemas and multi-page mathematics text can take longer than
        # section selection. Keep a bounded timeout while allowing generation/review.
        client = OpenAI(api_key=self.api_key, timeout=180.0, max_retries=2)
        try:
            response = client.responses.parse(
                model=self.model,
                instructions=instructions,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=schema,
                store=False,
            )
        except AuthenticationError as error:
            raise RuntimeError(
                "OpenAI APIの認証に失敗しました。APIキーを再確認してください。"
            ) from error
        except RateLimitError as error:
            raise RuntimeError(
                "OpenAI APIの利用上限または課金上限に達しました。APIのBillingとUsageを確認してください。"
            ) from error
        except BadRequestError as error:
            message = getattr(error, "message", "")
            raise RuntimeError(
                "OpenAI APIがリクエストを受理できませんでした。"
                f"モデル名または構造化出力を確認してください。 ({message})"
            ) from error
        except APIConnectionError as error:
            raise RuntimeError(
                "バックエンドからOpenAI APIへ接続できませんでした。"
                f"原因: {safe_connection_reason(error)}"
            ) from error
        except APIStatusError as error:
            raise RuntimeError(
                f"OpenAI APIでエラーが発生しました。HTTP {error.status_code}"
            ) from error
        if response.status != "completed" or response.output_parsed is None:
            raise RuntimeError("OpenAI returned an incomplete or empty response")
        return response.output_parsed


SELECTION_INSTRUCTIONS = """You select the smallest set of relevant PDF outline sections for a mathematics learning goal. Use only outline facts. Do not treat document order as conceptual dependency. Do not invent sections. Respect limits. Return page ranges and concise rationale. This does not guarantee mathematical correctness or completeness."""

GENERATION_INSTRUCTIONS = """Generate a minimal candidate concept dependency DAG for the stated mathematics goal from only the supplied page-numbered text. Distinguish PDF statements from inference. Do not treat table-of-contents order as dependency. Deduplicate spelling variants, distinguish definitions and theorems, avoid irrelevant detail, and never claim correctness or completeness. Every PDF-derived node must have page evidence. Anything necessary but unsupported by the PDF must be sourceType external-prerequisite-suggestion, included false, importance supporting, and have no fabricated page. All nodes and edges are unconfirmed. Use exactly one goal node. Dependencies point prerequisite -> dependent. Lower confidence for uncertain relations."""

REVIEW_INSTRUCTIONS = """Critically review the supplied candidate instead of defending it. Look for missing or unnecessary prerequisites, wrong direction, duplicates, source mismatch, excessive detail, paths that do not reach the goal, and claims beyond the supplied PDF text. Report issues only; do not silently rewrite or approve the graph. Absence of issues does not guarantee completeness or correctness."""


class LearningMapAIService:
    def __init__(self, client: StructuredClient):
        self.client = client

    def select_sections(self, payload: dict) -> SelectionResponse:
        return self.client.create(
            schema=SelectionResponse,
            instructions=SELECTION_INSTRUCTIONS,
            payload=payload,
        )

    def generate(self, payload: dict) -> GeneratedGraph:
        return self.client.create(
            schema=GeneratedGraph, instructions=GENERATION_INSTRUCTIONS, payload=payload
        )

    def review(self, payload: dict) -> ReviewResponse:
        return self.client.create(
            schema=ReviewResponse, instructions=REVIEW_INSTRUCTIONS, payload=payload
        )

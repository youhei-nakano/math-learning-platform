import os
import unicodedata
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .openai_service import LearningMapAIService, OpenAIStructuredClient
from .schemas import (
    GeneratedGraph,
    GenerateRequest,
    ReviewRequest,
    ReviewResponse,
    SelectionRequest,
    SelectionResponse,
)
from .validation import (
    GraphValidationError,
    downgrade_unreachable_required_nodes,
    reject_unsupplied_evidence,
    validate_graph,
)

app = FastAPI(title="Math Learning Map API", version="0.1.0")
configured_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = sorted(
    {origin.strip() for origin in configured_origins.split(",") if origin.strip()}
    | {"http://localhost:5173", "http://127.0.0.1:5173"}
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_ai_service() -> LearningMapAIService:
    return LearningMapAIService(OpenAIStructuredClient())


def normalize_outline_title(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", value).casefold().split())


@app.exception_handler(GraphValidationError)
async def graph_validation_handler(_request: Request, error: GraphValidationError):
    return JSONResponse(status_code=422, content={"detail": error.errors})


@app.get("/health")
def health():
    client = OpenAIStructuredClient()
    return {
        "status": "ok",
        "aiAvailable": client.available,
        "model": client.model if client.available else None,
        "configurationError": client.configuration_error,
    }


@app.post("/api/learning-map/select-sections", response_model=SelectionResponse)
def select_sections(
    request: SelectionRequest,
    service: Annotated[LearningMapAIService, Depends(get_ai_service)],
):
    try:
        result = service.select_sections(request.model_dump())
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    outline = {item.id: item for item in request.outline}
    if len(result.sections) > request.maxSections:
        raise GraphValidationError(["section limit exceeded"])
    total_pages = set()
    resolved = [item for item in request.outline if item.pdfPage is not None]
    normalized = []
    warnings = list(result.warnings)
    for section in result.sections:
        selected = outline.get(section.outlineId)
        if selected is None:
            matching_titles = [
                item
                for item in request.outline
                if normalize_outline_title(item.title)
                == normalize_outline_title(section.title)
            ]
            if len(matching_titles) == 1:
                selected = matching_titles[0]
                warnings.append(
                    f"AIの章節ID {section.outlineId} をタイトル一致により"
                    f" {selected.id} へ補正しました。"
                )
            else:
                warnings.append(
                    f"アウトラインと照合できないAI候補を除外しました: "
                    f"{section.title} ({section.outlineId})"
                )
                continue
        if selected.pdfPage is None:
            warnings.append(
                f"開始ページを解決できないAI候補を除外しました: {selected.title}"
            )
            continue
        next_page = next(
            (
                item.pdfPage
                for item in resolved
                if item.pdfPage is not None and item.pdfPage > selected.pdfPage
            ),
            request.pageCount + 1,
        )
        end_page = min(request.pageCount, next_page - 1)
        normalized_section = section.model_copy(
            update={
                "outlineId": selected.id,
                "title": selected.title,
                "startPage": selected.pdfPage,
                "endPage": end_page,
            }
        )
        normalized.append(normalized_section)
        total_pages.update(range(selected.pdfPage, end_page + 1))
    if len(total_pages) > request.maxPages:
        raise GraphValidationError(["page limit exceeded"])
    if not normalized:
        raise GraphValidationError(
            [
                "AIが選定した章節をPDFアウトラインと照合できませんでした。再試行してください。"
            ]
        )
    return SelectionResponse(sections=normalized, warnings=warnings)


@app.post("/api/learning-map/generate", response_model=GeneratedGraph)
def generate(
    request: GenerateRequest,
    service: Annotated[LearningMapAIService, Depends(get_ai_service)],
):
    if len({page.page for page in request.pages}) > request.maxPages:
        raise GraphValidationError(["page limit exceeded"])
    if any(page.page > request.pageCount for page in request.pages):
        raise GraphValidationError(["page out of range"])
    try:
        result = service.generate(request.model_dump())
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    if not result.nodes:
        raise GraphValidationError(["AI returned an empty graph"])
    reject_unsupplied_evidence(
        result, {page.page for page in request.pages}, request.pageCount
    )
    downgrade_unreachable_required_nodes(result)
    validate_graph(
        result,
        request.pageCount,
        request.maxNodes,
        {page.page for page in request.pages},
    )
    return result


@app.post("/api/learning-map/review", response_model=ReviewResponse)
def review(
    request: ReviewRequest,
    service: Annotated[LearningMapAIService, Depends(get_ai_service)],
):
    validate_graph(
        request.graph,
        request.pageCount,
        allowed_pages={page.page for page in request.pages},
    )
    try:
        return service.review(request.model_dump())
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

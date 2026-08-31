from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Confidence = Literal["low", "medium", "high"]
Confirmation = Literal["unconfirmed", "confirmed", "rejected"]
NodeType = Literal[
    "concept",
    "definition",
    "example",
    "counterexample",
    "lemma",
    "theorem",
    "proofTechnique",
    "goal",
]
EdgeType = Literal[
    "definition-required",
    "theorem-required",
    "used-in-proof",
    "calculation-required",
    "helpful",
    "optional-for-goal",
]


class OutlineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    level: int = Field(ge=0)
    pdfPage: int | None = Field(default=None, ge=1)
    parentId: str | None = None


class SelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    author: str
    pageCount: int = Field(ge=1)
    outline: list[OutlineItem]
    goal: str = Field(min_length=1, max_length=500)
    understandingLevel: str = Field(min_length=1, max_length=200)
    maxSections: int = Field(default=10, ge=1, le=20)
    maxPages: int = Field(default=50, ge=1, le=50)


class SelectedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outlineId: str
    title: str
    startPage: int = Field(ge=1)
    endPage: int = Field(ge=1)
    rationale: str
    confidence: Confidence

    @model_validator(mode="after")
    def ordered(self):
        if self.endPage < self.startPage:
            raise ValueError("endPage must be greater than or equal to startPage")
        return self


class SelectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sections: list[SelectedSection]
    warnings: list[str]


class PageText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(ge=1)
    text: str = Field(min_length=20)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    description: str


class LearningNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    canonicalName: str
    aliases: list[str]
    type: NodeType
    reason: str
    relationToGoal: str
    understandingLevel: str
    completionCriteria: str
    importance: Literal["required", "recommended", "supporting"]
    sourcePages: list[int]
    sourceSections: list[str]
    evidence: list[Evidence]
    confidence: Confidence
    confirmationStatus: Confirmation = "unconfirmed"
    included: bool = True
    sourceType: Literal["pdf-evidence", "external-prerequisite-suggestion"]


class LearningEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    sourceId: str
    targetId: str
    type: EdgeType
    rationale: str
    evidencePages: list[int]
    confidence: Confidence
    confirmationStatus: Confirmation = "unconfirmed"
    relationKind: Literal[
        "ai-concept-dependency", "document-structure", "user-confirmed"
    ]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    author: str
    pageCount: int = Field(ge=1)
    goal: str
    understandingLevel: str
    sections: list[SelectedSection]
    pages: list[PageText]
    maxNodes: int = Field(default=30, ge=1, le=30)
    maxPages: int = Field(default=50, ge=1, le=50)


class GeneratedGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodes: list[LearningNode]
    edges: list[LearningEdge]
    warnings: list[str]


class ReviewIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    targetKind: Literal["node", "edge", "graph"]
    targetId: str
    type: Literal[
        "missing-prerequisite",
        "unnecessary-prerequisite",
        "wrong-direction",
        "duplicate-node",
        "source-mismatch",
        "excessive-detail",
        "no-path-to-goal",
        "beyond-source",
    ]
    description: str
    check: str
    severity: Literal["low", "medium", "high"]
    resolved: bool = False


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pageCount: int = Field(ge=1)
    goal: str
    pages: list[PageText]
    graph: GeneratedGraph


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issues: list[ReviewIssue]
    summary: str
    warnings: list[str]

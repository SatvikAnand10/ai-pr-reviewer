from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Issue(BaseModel):
    severity: Severity
    title: str = Field(..., description="Short title of the issue")
    description: str = Field(..., description="Explanation of the issue")
    file: Optional[str] = Field(None, description="File path the issue applies to")
    line: Optional[int] = Field(None, description="Line number the issue applies to")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class ReviewResult(BaseModel):
    summary: str = Field(..., description="High-level summary of the diff")
    issues: list[Issue] = Field(default_factory=list)
    overall_assessment: Literal["approve", "request_changes", "comment"]


class ReviewRequest(BaseModel):
    diff: str = Field(..., min_length=1, description="Unified diff to review")
    provider: Optional[Literal["claude", "groq"]] = Field(
        None, description="LLM provider override; falls back to DEFAULT_PROVIDER"
    )
    context: Optional[str] = Field(None, description="Additional PR context, e.g. description")
    language: Optional[str] = Field(None, description="Primary language of the diff")


class ReviewResponse(BaseModel):
    provider: str
    result: ReviewResult


class ReviewRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    provider: str
    diff: str
    summary: str
    issues: list[Issue]
    overall_assessment: Literal["approve", "request_changes", "comment"]

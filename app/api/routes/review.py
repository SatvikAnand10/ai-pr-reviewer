from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.db.models import ReviewRecord
from app.schemas.review import ReviewRecordOut, ReviewRequest, ReviewResponse
from app.services.llm.exceptions import LLMGenerationError
from app.services.reviewer import ReviewerService

router = APIRouter(prefix="/api/v1", tags=["review"])


def get_reviewer_service(settings: Settings = Depends(get_settings)) -> ReviewerService:
    return ReviewerService(settings=settings)


@router.post("/review", response_model=ReviewResponse)
async def review_diff(
    request: ReviewRequest,
    reviewer: ReviewerService = Depends(get_reviewer_service),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    provider = request.provider or reviewer.settings.default_provider
    try:
        result = await reviewer.review(request)
    except LLMGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    record = ReviewRecord(
        provider=provider,
        diff=request.diff,
        summary=result.summary,
        issues=[issue.model_dump(mode="json") for issue in result.issues],
        overall_assessment=result.overall_assessment,
    )
    db.add(record)
    await db.commit()

    return ReviewResponse(provider=provider, result=result)


@router.get("/reviews", response_model=list[ReviewRecordOut])
async def list_reviews(db: AsyncSession = Depends(get_db)) -> list[ReviewRecord]:
    result = await db.execute(
        select(ReviewRecord).order_by(ReviewRecord.created_at.desc()).limit(20)
    )
    return list(result.scalars().all())

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.schemas.review import ReviewRequest, ReviewResponse
from app.services.llm.exceptions import LLMGenerationError
from app.services.reviewer import ReviewerService

router = APIRouter(prefix="/api/v1", tags=["review"])


def get_reviewer_service(settings: Settings = Depends(get_settings)) -> ReviewerService:
    return ReviewerService(settings=settings)


@router.post("/review", response_model=ReviewResponse)
async def review_diff(
    request: ReviewRequest,
    reviewer: ReviewerService = Depends(get_reviewer_service),
) -> ReviewResponse:
    provider = request.provider or reviewer.settings.default_provider
    try:
        result = await reviewer.review(request)
    except LLMGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ReviewResponse(provider=provider, result=result)

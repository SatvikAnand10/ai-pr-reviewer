from app.core.config import Settings
from app.schemas.review import ReviewRequest, ReviewResult
from app.services.llm.factory import get_llm_client
from app.services.prompts import build_review_prompt


class ReviewerService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def review(self, request: ReviewRequest) -> ReviewResult:
        provider = request.provider or self.settings.default_provider
        client = get_llm_client(provider, self.settings)
        prompt = build_review_prompt(
            diff=request.diff, context=request.context, language=request.language
        )
        return await client.generate_review(prompt)

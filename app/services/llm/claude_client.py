from anthropic import APIError, AsyncAnthropic
from pydantic import ValidationError

from app.schemas.review import ReviewResult
from app.services.llm.base import LLMClient
from app.services.llm.exceptions import LLMGenerationError

_REVIEW_TOOL_NAME = "submit_review"


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMGenerationError("ANTHROPIC_API_KEY is not configured")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate_review(self, prompt: str) -> ReviewResult:
        schema = ReviewResult.model_json_schema()
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                tools=[
                    {
                        "name": _REVIEW_TOOL_NAME,
                        "description": "Submit the structured code review result.",
                        "input_schema": schema,
                    }
                ],
                tool_choice={"type": "tool", "name": _REVIEW_TOOL_NAME},
                messages=[{"role": "user", "content": prompt}],
            )
        except APIError as exc:
            raise LLMGenerationError(f"Claude request failed: {exc}") from exc

        for block in response.content:
            if block.type == "tool_use" and block.name == _REVIEW_TOOL_NAME:
                try:
                    return ReviewResult.model_validate(block.input)
                except ValidationError as exc:
                    raise LLMGenerationError(
                        f"Claude returned a review that failed validation: {exc}"
                    ) from exc

        raise LLMGenerationError("Claude did not return a structured review")

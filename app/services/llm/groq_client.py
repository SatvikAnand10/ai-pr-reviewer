import json

from groq import APIError
from groq import AsyncGroq
from pydantic import ValidationError

from app.schemas.review import ReviewResult
from app.services.llm.base import LLMClient
from app.services.llm.exceptions import LLMGenerationError


class GroqClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMGenerationError("GROQ_API_KEY is not configured")
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def generate_review(self, prompt: str) -> ReviewResult:
        schema = ReviewResult.model_json_schema()
        system_prompt = (
            "You are a strict code review assistant. Respond with a single JSON object "
            "that matches this JSON schema exactly, with no extra commentary or markdown "
            f"fences:\n{json.dumps(schema)}"
        )
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
        except APIError as exc:
            raise LLMGenerationError(f"Groq request failed: {exc}") from exc

        content = response.choices[0].message.content or ""
        try:
            data = json.loads(content)
            return ReviewResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMGenerationError(
                f"Groq returned a review that failed validation: {exc}"
            ) from exc

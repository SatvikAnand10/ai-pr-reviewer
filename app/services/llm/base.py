from abc import ABC, abstractmethod

from app.schemas.review import ReviewResult


class LLMClient(ABC):
    @abstractmethod
    async def generate_review(self, prompt: str) -> ReviewResult:
        """Send the prompt to the provider and return a validated ReviewResult."""

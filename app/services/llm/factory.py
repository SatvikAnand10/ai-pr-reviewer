from app.core.config import Settings
from app.services.llm.base import LLMClient
from app.services.llm.claude_client import ClaudeClient
from app.services.llm.exceptions import LLMGenerationError
from app.services.llm.groq_client import GroqClient


def get_llm_client(provider: str, settings: Settings) -> LLMClient:
    if provider == "claude":
        return ClaudeClient(api_key=settings.anthropic_api_key, model=settings.claude_model)
    if provider == "groq":
        return GroqClient(api_key=settings.groq_api_key, model=settings.groq_model)
    raise LLMGenerationError(f"Unknown provider: {provider}")

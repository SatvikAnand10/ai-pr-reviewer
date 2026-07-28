import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.routes.review import get_reviewer_service
from app.core.config import Settings, get_settings
from app.schemas.review import ReviewRequest, ReviewResult
from app.services.github_client import GitHubClient
from app.services.llm.exceptions import LLMGenerationError
from app.services.reviewer import ReviewerService

router = APIRouter(prefix="/api/v1", tags=["webhook"])
logger = logging.getLogger(__name__)

HANDLED_ACTIONS = {"opened", "synchronize"}


def get_github_client(settings: Settings = Depends(get_settings)) -> GitHubClient:
    return GitHubClient(settings=settings)


def _verify_signature(secret: str, payload_body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


def _format_comment(result: ReviewResult) -> str:
    lines = [f"### AI PR Review\n\n{result.summary}"]
    if result.issues:
        lines.append("\n| Severity | Title | File | Line | Suggestion |")
        lines.append("|---|---|---|---|---|")
        for issue in result.issues:
            lines.append(
                f"| {issue.severity.value} | {issue.title} | {issue.file or '-'} "
                f"| {issue.line if issue.line is not None else '-'} | {issue.suggestion or '-'} |"
            )
    lines.append(f"\n**Overall assessment:** {result.overall_assessment}")
    return "\n".join(lines)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
    settings: Settings = Depends(get_settings),
    github_client: GitHubClient = Depends(get_github_client),
    reviewer: ReviewerService = Depends(get_reviewer_service),
) -> dict:
    raw_body = await request.body()

    if not _verify_signature(settings.github_webhook_secret, raw_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": "not a pull_request event"}

    payload = await request.json()
    action = payload.get("action")
    if action not in HANDLED_ACTIONS:
        return {"status": "ignored", "reason": f"unhandled action: {action}"}

    pull_request = payload["pull_request"]
    repository = payload["repository"]
    owner = repository["owner"]["login"]
    repo = repository["name"]
    pull_number = pull_request["number"]
    installation_id = payload["installation"]["id"]

    installation_token = await github_client.get_installation_token(installation_id)
    diff = await github_client.get_pull_request_diff(owner, repo, pull_number, installation_token)

    try:
        result = await reviewer.review(
            ReviewRequest(diff=diff, context=pull_request.get("title"))
        )
    except LLMGenerationError as exc:
        logger.error("Review generation failed for PR #%s: %s", pull_number, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    await github_client.post_pull_request_comment(
        owner, repo, pull_number, _format_comment(result), installation_token
    )

    return {"status": "reviewed", "pull_request": pull_number}

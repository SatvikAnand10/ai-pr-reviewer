import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.api.routes.review import get_reviewer_service
from app.api.routes.webhook import get_github_client
from app.core.config import get_settings
from app.main import app
from app.schemas.review import ReviewRequest, ReviewResult

WEBHOOK_SECRET = "test-secret"

PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "number": 42,
        "title": "Add feature X",
    },
    "repository": {
        "name": "ai-pr-reviewer",
        "owner": {"login": "SatvikAnand10"},
    },
    "installation": {"id": 123456},
}


class FakeSettings:
    default_provider = "claude"
    github_webhook_secret = WEBHOOK_SECRET


class FakeReviewerService:
    settings = FakeSettings()

    async def review(self, request: ReviewRequest) -> ReviewResult:
        return ReviewResult(
            summary="Looks fine overall",
            issues=[],
            overall_assessment="approve",
        )


class FakeGitHubClient:
    def __init__(self):
        self.installation_ids: list[int] = []
        self.diff_requests: list[tuple[str, str, int]] = []
        self.posted_comments: list[dict] = []

    async def get_installation_token(self, installation_id: int) -> str:
        self.installation_ids.append(installation_id)
        return "fake-installation-token"

    async def get_pull_request_diff(
        self, owner: str, repo: str, pull_number: int, installation_token: str
    ) -> str:
        self.diff_requests.append((owner, repo, pull_number))
        return "diff --git a/app/foo.py b/app/foo.py\n+def foo():\n+    pass"

    async def post_pull_request_comment(
        self, owner: str, repo: str, pull_number: int, body: str, installation_token: str
    ) -> None:
        self.posted_comments.append(
            {"owner": owner, "repo": repo, "pull_number": pull_number, "body": body}
        )


def _sign(body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def fake_github_client():
    return FakeGitHubClient()


@pytest.fixture
def client(fake_github_client):
    app.dependency_overrides[get_settings] = lambda: FakeSettings()
    app.dependency_overrides[get_reviewer_service] = lambda: FakeReviewerService()
    app.dependency_overrides[get_github_client] = lambda: fake_github_client
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_webhook_rejects_invalid_signature(client):
    raw_body = json.dumps(PAYLOAD).encode()
    response = client.post(
        "/api/v1/webhook",
        content=raw_body,
        headers={
            "X-Hub-Signature-256": "sha256=deadbeef",
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_webhook_rejects_missing_signature(client):
    raw_body = json.dumps(PAYLOAD).encode()
    response = client.post(
        "/api/v1/webhook",
        content=raw_body,
        headers={
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_webhook_triggers_review_and_comment(client, fake_github_client):
    raw_body = json.dumps(PAYLOAD).encode()
    response = client.post(
        "/api/v1/webhook",
        content=raw_body,
        headers={
            "X-Hub-Signature-256": _sign(raw_body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "reviewed", "pull_request": 42}

    assert fake_github_client.installation_ids == [123456]
    assert fake_github_client.diff_requests == [("SatvikAnand10", "ai-pr-reviewer", 42)]
    assert len(fake_github_client.posted_comments) == 1
    comment = fake_github_client.posted_comments[0]
    assert comment["pull_number"] == 42
    assert "Looks fine overall" in comment["body"]


def test_webhook_ignores_non_pull_request_event(client, fake_github_client):
    raw_body = json.dumps(PAYLOAD).encode()
    response = client.post(
        "/api/v1/webhook",
        content=raw_body,
        headers={
            "X-Hub-Signature-256": _sign(raw_body),
            "X-GitHub-Event": "issues",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert fake_github_client.installation_ids == []


def test_webhook_ignores_unhandled_action(client, fake_github_client):
    payload = {**PAYLOAD, "action": "closed"}
    raw_body = json.dumps(payload).encode()
    response = client.post(
        "/api/v1/webhook",
        content=raw_body,
        headers={
            "X-Hub-Signature-256": _sign(raw_body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert fake_github_client.installation_ids == []

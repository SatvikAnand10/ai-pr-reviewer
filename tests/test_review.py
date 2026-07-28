import pytest
from fastapi.testclient import TestClient

from app.api.routes.review import get_reviewer_service
from app.db.database import get_db
from app.main import app
from app.schemas.review import ReviewRequest, ReviewResult


class FakeSettings:
    default_provider = "claude"


class FakeReviewerService:
    settings = FakeSettings()

    async def review(self, request: ReviewRequest) -> ReviewResult:
        return ReviewResult(
            summary="Looks fine overall",
            issues=[
                {
                    "severity": "low",
                    "title": "Missing docstring",
                    "description": "The new function has no docstring.",
                    "file": "app/foo.py",
                    "line": 12,
                    "suggestion": "Add a short docstring.",
                }
            ],
            overall_assessment="comment",
        )


class FakeSession:
    def add(self, obj) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, obj) -> None:
        pass


async def _fake_get_db():
    yield FakeSession()


@pytest.fixture
def client():
    app.dependency_overrides[get_reviewer_service] = lambda: FakeReviewerService()
    app.dependency_overrides[get_db] = _fake_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_review_endpoint_returns_structured_feedback(client):
    response = client.post(
        "/api/v1/review",
        json={"diff": "diff --git a/app/foo.py b/app/foo.py\n+def foo():\n+    pass"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "claude"
    assert body["result"]["overall_assessment"] == "comment"
    assert body["result"]["issues"][0]["severity"] == "low"


def test_review_endpoint_rejects_empty_diff(client):
    response = client.post("/api/v1/review", json={"diff": ""})
    assert response.status_code == 422

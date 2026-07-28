import time

import httpx
import jwt

from app.core.config import Settings

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    def __init__(self, settings: Settings):
        self.app_id = settings.github_app_id
        self.private_key_value = settings.github_private_key
        self.private_key_path = settings.github_private_key_path
        self._private_key: str | None = None

    def _load_private_key(self) -> str:
        if self._private_key is None:
            if self.private_key_value:
                self._private_key = self.private_key_value
            else:
                with open(self.private_key_path, encoding="utf-8") as f:
                    self._private_key = f.read()
        return self._private_key

    def _generate_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": int(self.app_id),
        }
        return jwt.encode(payload, self._load_private_key(), algorithm="RS256")

    async def get_installation_token(self, installation_id: int) -> str:
        app_jwt = self._generate_jwt()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            return response.json()["token"]

    async def get_pull_request_diff(
        self, owner: str, repo: str, pull_number: int, installation_token: str
    ) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}",
                headers={
                    "Authorization": f"Bearer {installation_token}",
                    "Accept": "application/vnd.github.v3.diff",
                },
            )
            response.raise_for_status()
            return response.text

    async def post_pull_request_comment(
        self, owner: str, repo: str, pull_number: int, body: str, installation_token: str
    ) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pull_number}/comments",
                headers={
                    "Authorization": f"Bearer {installation_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={"body": body},
            )
            response.raise_for_status()

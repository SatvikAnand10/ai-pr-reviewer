# AI PR Reviewer

An AI-powered code review service that plugs into GitHub. It automatically reviews pull requests using an LLM, returns structured, actionable feedback, tracks review history in Postgres, and posts the results directly as a PR comment — no manual triggering required.

**Live demo:** [ai-pr-reviewer-production-69d8.up.railway.app/dashboard](https://ai-pr-reviewer-production-69d8.up.railway.app/dashboard)

## Key Features

- **Pluggable LLM providers** — switch between Claude and Groq via config, no code changes
- **Structured review output** — severity-tagged issues (critical/high/medium/low/info) with file, line, description, and suggested fix, plus an overall assessment (`approve` / `request_changes` / `comment`)
- **Postgres persistence** — every review is saved and queryable via a history endpoint
- **GitHub webhook automation** — signature-verified `pull_request` events trigger an end-to-end review with zero manual steps
- **Dashboard** — a lightweight public page showing review stats, recent reviews, and an issue-count trend chart

## Tech Stack

- **Backend:** FastAPI, Pydantic
- **Database:** PostgreSQL via SQLAlchemy (async) + asyncpg
- **LLM providers:** Groq, Anthropic Claude
- **GitHub integration:** GitHub Apps (JWT + installation tokens via PyJWT), webhook signature verification
- **Deployment:** Railway

## Architecture

```
PR opened/updated on GitHub
        │
        ▼
GitHub webhook → POST /api/v1/webhook (HMAC signature verified)
        │
        ▼
GitHubClient authenticates as the GitHub App and fetches the PR diff
        │
        ▼
ReviewerService sends the diff to the configured LLM provider
        │
        ▼
Structured review result is saved to Postgres (ReviewRecord)
        │
        ▼
Review is posted back to the PR as a comment
```

The same review engine also powers a direct API (`POST /api/v1/review`) for reviewing an arbitrary diff without GitHub involved.

## Local Setup

```bash
git clone https://github.com/SatvikAnand10/ai-pr-reviewer.git
cd ai-pr-reviewer

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# fill in ANTHROPIC_API_KEY / GROQ_API_KEY, DATABASE_URL, GITHUB_APP_ID, etc.

uvicorn app.main:app --reload --port 8000
```

Run the test suite with:

```bash
pytest
```

## API Endpoints

| Method | Path                | Description                                              |
|--------|---------------------|------------------------------------------------------------|
| GET    | `/health`           | Health check                                              |
| POST   | `/api/v1/review`     | Submit a diff, get back a structured LLM review           |
| GET    | `/api/v1/reviews`    | List the 20 most recent stored reviews                    |
| POST   | `/api/v1/webhook`    | GitHub webhook receiver for `pull_request` events          |
| GET    | `/dashboard`         | Public HTML dashboard of review activity                  |

---

This is a portfolio/demo project built to showcase an end-to-end AI code review pipeline, not a production-hardened tool.

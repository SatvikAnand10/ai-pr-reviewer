from fastapi import FastAPI

from app.api.routes import health, review

app = FastAPI(title="AI PR Reviewer", version="0.1.0")

app.include_router(health.router)
app.include_router(review.router)

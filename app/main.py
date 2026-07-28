import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health, review
from app.db.database import Base, engine
from app.db.models import ReviewRecord  # noqa: F401  (registers model with Base.metadata)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        logger.warning(
            "Could not initialize database tables; is DATABASE_URL reachable?",
            exc_info=True,
        )
    yield


app = FastAPI(title="AI PR Reviewer", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(review.router)

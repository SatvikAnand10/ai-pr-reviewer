from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


def _build_engine_args(database_url: str) -> tuple[str, dict]:
    """Normalize a libpq-style Postgres URL for use with the asyncpg driver."""
    url = make_url(database_url)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    url = url.set(query=query)

    connect_args: dict = {}
    if sslmode and sslmode != "disable":
        connect_args["ssl"] = True

    return url.render_as_string(hide_password=False), connect_args


_database_url, _connect_args = _build_engine_args(settings.database_url)

engine = create_async_engine(_database_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

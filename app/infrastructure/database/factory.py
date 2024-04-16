import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import Settings

logger = logging.getLogger(__name__)


def make_connection_string(settings: Settings) -> str:
    result = (
        f"postgresql+asyncpg://{settings.user}:{settings.password}@{settings.host}:{settings.port}/{settings.name}"
        f"?async_fallback=True"
    )
    return result


def create_pool(url: str) -> sessionmaker:
    engine = create_async_engine(url)
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
        autoflush=False
    )

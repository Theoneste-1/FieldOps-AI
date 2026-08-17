from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug and settings.is_sqlite,
    future=True,
    connect_args=connect_args,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    if settings.auto_create_tables:
        from app.models import entities  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

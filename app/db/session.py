"""
Asynchronous database session management.

This module configures the SQLAlchemy async engine and session factory
used throughout the Tradequity backend.

Design principles:
    - Async PostgreSQL access via asyncpg.
    - Connection pooling for production workloads.
    - Clean session lifecycle management.
    - FastAPI dependency compatibility.
"""

from collections.abc        import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config        import settings

engine = create_async_engine(
    settings.database_url,
    # echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)


AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a scoped asynchronous database session.

    This dependency is intended for FastAPI route ingestion and ensures
    that each request receives an isolated SQLAlchemy async session.

    Sessions are automatically closed after request completion.

    Yields:
         AsyncSession:
            Active SQLAlchemy asynchronous session.
    """

    async with AsyncSessionFactory() as session:
        yield session

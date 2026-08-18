"""Database engine and session factory setup."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine as _create_async_engine,
)


def get_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the given database URL.

    Args:
        database_url: PostgreSQL connection string (asyncpg driver).

    Returns:
        Configured async_sessionmaker instance.
    """
    engine = _create_async_engine(
        database_url,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

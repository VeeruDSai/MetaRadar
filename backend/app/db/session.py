import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
async_session_factory = AsyncSessionLocal

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def try_advisory_lock(session: AsyncSession, lock_id: int) -> bool:
    """Tries to acquire a PostgreSQL advisory lock for single-execution scheduling protection."""
    try:
        result = await session.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id})
        return bool(result.scalar())
    except Exception as e:
        logger.warning(f"Advisory lock check failed: {e}")
        return False


async def release_advisory_lock(session: AsyncSession, lock_id: int) -> bool:
    """Releases a PostgreSQL advisory lock."""
    try:
        result = await session.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
        return bool(result.scalar())
    except Exception as e:
        logger.warning(f"Advisory unlock failed: {e}")
        return False

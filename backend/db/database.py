"""SQLAlchemy async database setup.
Uses SQLite (aiosqlite) for local dev and MySQL (aiomysql) for production.
Set USE_SQLITE=true in .env to force SQLite regardless of other settings.
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Pick driver ───────────────────────────────────────────────────────────────
if settings.use_sqlite:
    DATABASE_URL = f"sqlite+aiosqlite:///{settings.sqlite_path}"
    connect_args = {"check_same_thread": False}
else:
    DATABASE_URL = (
        f"mysql+aiomysql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    connect_args = {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create all tables on startup. Non-fatal if DB is unreachable."""
    from backend.models import user, trip  # noqa: F401 – register mappers
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready (%s).", DATABASE_URL.split("://")[0])
    except Exception as exc:
        logger.warning("DB init skipped (will retry on first request): %s", exc)


async def get_db():
    """FastAPI dependency that yields an async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

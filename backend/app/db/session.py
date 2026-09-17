from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_pre_ping=True
    )
except Exception as exc:
    if settings.ENVIRONMENT.lower() in ("production", "prod"):
        raise RuntimeError(
            f"Failed to initialize production PostgreSQL engine for URL '{db_url}': {exc}"
        ) from exc
    try:
        import aiosqlite  # noqa: F401
        fallback_url = "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(
            fallback_url,
            echo=False,
            future=True
        )
    except ImportError:
        raise RuntimeError(
            f"Failed to initialize database engine for '{db_url}': {exc}"
        ) from exc



AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database session to requests."""
    async with AsyncSessionLocal() as session:
        yield session

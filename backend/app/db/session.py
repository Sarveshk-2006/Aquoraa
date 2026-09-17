from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

db_url = settings.DATABASE_URL
try:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_pre_ping=True
    )
except Exception:
    db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True
    )


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

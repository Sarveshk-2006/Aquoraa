import redis.asyncio as redis
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.schemas.health import LivenessResponse, ReadinessResponse, ServicesHealth

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/live", response_model=LivenessResponse, summary="Application Process Liveness Check")
async def health_live() -> LivenessResponse:
    """
    Liveness check to verify if the application process is running.
    Does NOT require database or Redis connectivity.
    """
    return LivenessResponse(status="ok")

@router.get("/ready", response_model=ReadinessResponse, summary="Dependency Infrastructure Readiness Check")
async def health_ready(response: Response) -> ReadinessResponse:
    """
    Readiness check to verify PostgreSQL database and Redis connectivity.
    Returns HTTP 200 when all dependencies are healthy, or HTTP 503 when degraded.
    """
    db_status = "ok"
    redis_status = "ok"

    # 1. PostgreSQL Connectivity Check
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() != 1:
                db_status = "error"
    except Exception as e:  # noqa: BLE001
        logger.error("Database readiness check failed", error=str(e))
        db_status = "error"

    # 2. Redis Connectivity Check
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        ping_ok = await r.ping()
        await r.aclose()
        if not ping_ok:
            redis_status = "error"
    except Exception as e:  # noqa: BLE001
        logger.error("Redis readiness check failed", error=str(e))
        redis_status = "error"

    is_healthy = (db_status == "ok") and (redis_status == "ok")

    return ReadinessResponse(
        status="ok" if is_healthy else "degraded",
        environment=settings.ENVIRONMENT,
        services=ServicesHealth(
            database=db_status,
            redis=redis_status
        )
    )

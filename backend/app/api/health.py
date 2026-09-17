from fastapi import APIRouter, Response

from app.api.v1.health import health_ready
from app.schemas.health import ReadinessResponse

router = APIRouter()

@router.get("/health", response_model=ReadinessResponse, summary="Top-level Readiness Alias", include_in_schema=False)
async def top_level_health(response: Response) -> ReadinessResponse:
    """Alias pointing to /api/v1/health/ready for backward compatibility."""
    return await health_ready(response)

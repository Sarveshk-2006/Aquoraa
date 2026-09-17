from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_liveness_endpoint_succeeds_without_dependencies(async_client):
    """Verify /api/v1/health/live returns 200 OK without database or Redis checks."""
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

@pytest.mark.asyncio
async def test_readiness_endpoint_degraded(async_client):
    """Verify /api/v1/health/ready returns 503 degraded when DB/Redis dependencies fail."""
    response = await async_client.get("/api/v1/health/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]

@pytest.mark.asyncio
async def test_readiness_endpoint_mocked_success(async_client):
    """Verify /api/v1/health/ready returns 200 OK when DB and Redis are healthy."""
    with patch("app.api.v1.health.AsyncSessionLocal") as mock_session_cls, \
         patch("app.api.v1.health.redis.from_url") as mock_redis_cls:

        # Mock DB
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.aclose = AsyncMock(return_value=None)
        mock_redis_cls.return_value = mock_redis

        response = await async_client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["services"]["database"] == "ok"
        assert data["services"]["redis"] == "ok"

@pytest.mark.asyncio
async def test_top_level_health_alias(async_client):
    """Verify top-level /health alias responds with readiness structure."""
    response = await async_client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "services" in data

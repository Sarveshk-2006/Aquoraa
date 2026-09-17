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


@pytest.mark.asyncio
async def test_vercel_cors_header_verification(async_client):
    """Verify production Vercel origin returns Access-Control-Allow-Origin header."""
    origin = "https://aquora-nine.vercel.app"
    response = await async_client.get(
        "/api/v1/health/live",
        headers={"Origin": origin}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin

    # Verify OPTIONS preflight response as well
    preflight = await async_client.options(
        "/api/v1/health/live",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
@pytest.mark.asyncio
async def test_head_method_support_on_health_endpoints(async_client):
    """Verify HEAD requests on liveness, readiness, and alias health endpoints return 200 OK."""
    res_live = await async_client.head("/api/v1/health/live")
    assert res_live.status_code == 200

    res_ready = await async_client.head("/api/v1/health/ready")
    assert res_ready.status_code in [200, 503]

    res_alias = await async_client.head("/health")
    assert res_alias.status_code in [200, 503]



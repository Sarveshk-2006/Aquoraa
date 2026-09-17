import pytest


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    """Verify root endpoint returns project metadata and phase 1 context."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "tagline" in data
    assert "Phase 1" in data["phase"]
    assert "endpoints" in data
    assert data["endpoints"]["liveness"] == "/api/v1/health/live"
    assert data["endpoints"]["readiness"] == "/api/v1/health/ready"

import pytest


@pytest.mark.asyncio
async def test_request_id_generated_when_absent(async_client):
    """Verify X-Request-ID is generated and returned in headers when absent from request."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0

@pytest.mark.asyncio
async def test_request_id_propagated_when_supplied(async_client):
    """Verify incoming X-Request-ID header is preserved and echoed in response headers."""
    custom_id = "test-corr-id-12345"
    response = await async_client.get("/", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id

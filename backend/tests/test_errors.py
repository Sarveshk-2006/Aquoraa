import pytest
from app.core.exceptions import AppException
from app.main import app
from fastapi import APIRouter, HTTPException

# Register mock error router for exception handling verification
mock_error_router = APIRouter(prefix="/mock-errors", tags=["MockErrors"])

@mock_error_router.get("/app-error")
async def trigger_app_error():
    raise AppException(message="Resource invalid", code="INVALID_RESOURCE", status_code=400)

@mock_error_router.get("/http-error")
async def trigger_http_error():
    raise HTTPException(status_code=404, detail="Item not found")

app.include_router(mock_error_router)

@pytest.mark.asyncio
async def test_app_exception_payload(async_client):
    """Verify AppException produces standardized JSON payload with request_id and custom status."""
    response = await async_client.get("/mock-errors/app-error", headers={"X-Request-ID": "err-req-999"})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_RESOURCE"
    assert data["error"]["message"] == "Resource invalid"
    assert data["error"]["request_id"] == "err-req-999"

@pytest.mark.asyncio
async def test_validation_exception_payload(async_client):
    """Verify validation errors (422) return standardized error structure with request_id."""
    response = await async_client.get("/mock-errors/app-error?invalid_param=123", headers={"X-Request-ID": "err-req-777"})
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "request_id" in data["error"]

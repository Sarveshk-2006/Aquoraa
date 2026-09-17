"""Phase 16 — API Contract & Router Validation Tests.

Validates FastAPI endpoints across Phase 9-15 for response structure,
filtering capabilities, non-existent entity 404 status codes, and error formatting.
"""

from uuid import uuid4

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_api_alerts_list_endpoint():
    """Verify GET /api/v1/alerts endpoint returns 200 OK with valid list schema."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_api_alerts_get_nonexistent_id_404():
    """Verify GET /api/v1/alerts/{alert_id} returns 404 Not Found for invalid ID."""
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/alerts/{fake_id}")
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_api_alerts_configuration_endpoint():
    """Verify GET /api/v1/alerts/configuration returns system alert thresholds."""
    response = client.get("/api/v1/alerts/configuration")
    assert response.status_code == 200
    config_data = response.json()
    assert "thresholds" in config_data
    assert "ALERT_FLOOD_ONSET_LOOKAHEAD_MINUTES" in config_data["thresholds"]

"""
Phase 15 Production Database Schema, Migration Chain, Alert Service, and Endpoints Test Suite.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.db.init_db import REQUIRED_PRODUCTION_TABLES, apply_alembic_migrations, verify_production_schema
from app.db.session import get_db
from app.main import app
from app.services.alerts_service import AlertsService


client = TestClient(app)


def test_alembic_migration_head_is_0013_phase15_alerts():
    """Verify Alembic migration script location and single head 0013_phase15_alerts."""
    from alembic.script import ScriptDirectory
    from alembic.config import Config
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_ini_path = backend_dir / "alembic.ini"
    
    assert alembic_ini_path.exists(), "alembic.ini must exist in backend directory"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    script = ScriptDirectory.from_config(alembic_cfg)

    heads = script.get_heads()
    assert len(heads) == 1, f"Expected exactly 1 migration head, got {heads}"
    assert heads[0] == "0013_phase15_alerts", f"Expected head '0013_phase15_alerts', got '{heads[0]}'"


def test_required_production_tables_list():
    """Verify that all required production tables are tracked for schema verification."""
    expected_tables = [
        "audit_events",
        "rainfall_observation_grids",
        "terrain_datasets",
        "drainage_networks",
        "flood_simulation_runs",
        "digital_twin_runs",
        "digital_twin_slices",
        "routing_runs",
        "critical_facilities",
        "protect_city_runs",
        "ground_truth_runs",
        "simulator_scenarios",
        "simulator_runs",
        "alerts",
    ]
    for table in expected_tables:
        assert table in REQUIRED_PRODUCTION_TABLES


@pytest.mark.asyncio
async def test_schema_verification_detects_missing_tables():
    """Verify verify_production_schema returns missing tables when query reports empty."""
    with patch("app.db.init_db.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_res)
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        missing = await verify_production_schema()
        assert len(missing) == len(REQUIRED_PRODUCTION_TABLES), "Expected all tables to be flagged as missing"


@pytest.mark.asyncio
async def test_alerts_service_rollback_on_failed_transaction():
    """Verify AlertsService executes db.rollback() when database error occurs."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("Synthetic DB Error")

    service = AlertsService(db=mock_db)
    result = await service._find_active_alert_by_fingerprint("test_fingerprint")

    mock_db.rollback.assert_called_once()
    assert result is None


def test_health_live_endpoint():
    """Verify /api/v1/health/live returns HTTP 200."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_endpoint_with_cors():
    """Verify /api/v1/health/ready handles request and CORS origin header."""
    response = client.get("/api/v1/health/ready", headers={"Origin": "https://aquora-nine.vercel.app"})
    assert response.status_code in (200, 503)
    assert response.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"


def test_alerts_list_endpoint():
    """Verify GET /api/v1/alerts returns HTTP 200 with CORS headers."""
    response = client.get("/api/v1/alerts", headers={"Origin": "https://aquora-nine.vercel.app"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"
    data = response.json()
    assert "total_count" in data
    assert "alerts" in data


def test_simulator_scenarios_list_and_post_endpoints():
    """Verify Simulator GET and POST endpoints handle requests cleanly with mock AsyncSession."""
    async def override_get_db():
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_res
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        get_res = client.get("/api/v1/simulator/scenarios", headers={"Origin": "https://aquora-nine.vercel.app"})
        assert get_res.status_code == 200
        assert get_res.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"

        post_payload = {
            "baseline_run_id": "dt_test_baseline",
            "scenario_type": "RAINFALL_MULTIPLIER",
            "parameters": {"multiplier": 1.5},
            "assumptions": [
                {
                    "assumption_type": "RAINFALL_PROFILE",
                    "assumption_value": "UNIFORM_1.5X",
                    "assumption_source": "TEST",
                    "assumption_description": "1.5x uniform rainfall multiplier test"
                }
            ]
        }
        post_res = client.post("/api/v1/simulator/scenarios", json=post_payload, headers={"Origin": "https://aquora-nine.vercel.app"})
        assert post_res.status_code == 201
        assert post_res.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_digital_twin_latest_endpoint():
    """Verify GET /api/v1/digital-twin/runs/latest returns HTTP 200."""
    response = client.get("/api/v1/digital-twin/runs/latest", headers={"Origin": "https://aquora-nine.vercel.app"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"


def test_critical_access_facilities_endpoint():
    """Verify GET /api/v1/critical-access/facilities returns HTTP 200 with facilities."""
    response = client.get("/api/v1/critical-access/facilities", headers={"Origin": "https://aquora-nine.vercel.app"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"


def test_protect_city_latest_endpoint():
    """Verify GET /api/v1/protect-city/runs/latest returns HTTP 200."""
    response = client.get("/api/v1/protect-city/runs/latest", headers={"Origin": "https://aquora-nine.vercel.app"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"

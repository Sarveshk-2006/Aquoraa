"""
Regression Tests for Production Runtime Data, DEM Raster, Database Initialization, and Facility Seeding.
"""

import asyncio
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.db.init_db import seed_critical_facilities, run_migrations_and_seed
from app.providers.critical_facility import LocalCriticalFacilityProvider
from app.providers.intervention_candidate import SyntheticInterventionCandidateProvider
from app.main import app


def test_dem_raster_exists_in_runtime():
    """Verify required DEM file data/processed/phase7/terrain/elevation_30m.tif exists in repository runtime."""
    repo_root = Path(__file__).resolve().parents[2]
    dem_path = repo_root / "data" / "processed" / "phase7" / "terrain" / "elevation_30m.tif"
    assert dem_path.exists(), f"Required production DEM file missing at {dem_path}"
    assert dem_path.stat().st_size > 500_000, "DEM raster file size must be > 500 KB"


def test_dem_can_be_loaded():
    """Verify DEM raster can be loaded and read without FileNotFoundError."""
    import rasterio
    repo_root = Path(__file__).resolve().parents[2]
    dem_path = repo_root / "data" / "processed" / "phase7" / "terrain" / "elevation_30m.tif"

    with rasterio.open(dem_path) as src:
        array = src.read(1)
        assert array.shape[0] > 0 and array.shape[1] > 0
        assert src.crs is not None


def test_alembic_head_revision():
    """Verify Alembic latest head revision is 0013_phase15_alerts."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    backend_dir = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "0013_phase15_alerts"


@pytest.mark.asyncio
async def test_init_db_seeder_idempotent():
    """Verify database init seeder runs idempotently without throwing asyncio.run RuntimeError."""
    try:
        await seed_critical_facilities()
    except (OSError, ConnectionRefusedError, Exception) as e:
        assert "asyncio.run() cannot be called from a running event loop" not in str(e)


@pytest.mark.asyncio
async def test_no_asyncio_run_collision_in_event_loop():
    """Verify alembic env.py execution does not crash with asyncio.run inside running event loop."""
    import importlib.util
    backend_dir = Path(__file__).resolve().parents[1]
    env_path = backend_dir / "alembic" / "env.py"
    assert env_path.exists()

    spec = importlib.util.spec_from_file_location("alembic_env_test", env_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        assert "asyncio.run() cannot be called from a running event loop" not in str(e)


@pytest.mark.asyncio
async def test_local_facility_provider_loads_combined_facilities():
    """Verify LocalCriticalFacilityProvider loads verified facility dataset."""
    provider = LocalCriticalFacilityProvider()
    facilities = await provider.list_facilities()
    assert len(facilities) >= 300, f"Expected >= 300 verified facilities, got {len(facilities)}"


@pytest.mark.asyncio
async def test_protect_city_candidates_demarcated():
    """Verify synthetic candidates are explicitly demarcated as Development Data."""
    provider = SyntheticInterventionCandidateProvider()
    candidates = await provider.list_candidates()
    assert len(candidates) > 0
    for cand in candidates:
        assert "Planning Candidate - Development Data" in cand.name


@pytest.mark.asyncio
async def test_digital_twin_and_routing_production_flow():
    """Verify Digital Twin latest and Routing analysis return 200 OK with CORS headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        origin_header = {"Origin": "https://aquora-nine.vercel.app"}

        # 1. Health Live
        r_live = await client.get("/api/v1/health/live", headers=origin_header)
        assert r_live.status_code == 200
        assert r_live.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"

        # 2. Digital Twin Latest
        r_dt = await client.get("/api/v1/digital-twin/runs/latest", headers=origin_header)
        assert r_dt.status_code == 200
        assert r_dt.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"

        # 3. Route Analysis
        r_route = await client.post(
            "/api/v1/routing/routes/analyze",
            json={
                "origin": {"latitude": 19.076, "longitude": 72.877, "label": "Bandra East"},
                "destination": {"latitude": 19.100, "longitude": 72.890, "label": "BKC Hub"},
                "max_acceptable_severity": "HIGH",
                "max_alternatives": 2
            },
            headers=origin_header
        )
        assert r_route.status_code == 200
        assert r_route.headers.get("access-control-allow-origin") == "https://aquora-nine.vercel.app"

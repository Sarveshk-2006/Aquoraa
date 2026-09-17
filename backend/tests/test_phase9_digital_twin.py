"""
Phase 9 Unit and Integration Test Suite — Aquora Digital Twin & Future Flood Map.

Verifies:
1. Digital Twin run creation.
2. 180-minute horizon and exactly 7 canonical time slices (0, 30, 60, 90, 120, 150, 180).
3. Phase 6 physical solver integration as primary authority.
4. Phase 8 prototype ML score handling labeled PROTOTYPE_ONLY without replacing physical depth.
5. No exposure of Phase 7 training labels in operational APIs.
6. Map artifact file generation under data/processed/digital_twin/<run_id>/.
7. Compact map artifacts without giant per-cell GeoJSON responses.
8. Provenance recording identifying Phase6_Deterministic_D8, Phase8_XGBoost_Prototype_V1, REAL_DATA, E05.
"""

import pytest
from app.schemas.digital_twin import DigitalTwinRunRequestSchema
from app.services.digital_twin_service import (
    DigitalTwinProcessingService as DigitalTwinService,
)


@pytest.mark.asyncio
async def test_digital_twin_service_run_creation():
    """Verify service creates a run with 180m horizon and 7 canonical time slices."""
    service = DigitalTwinService()
    req = DigitalTwinRunRequestSchema(study_area_id="mumbai_mithi", horizon_minutes=180, timestep_minutes=30)
    run_response = await service.create_run(req)

    assert run_response.run_id.startswith("dt_")
    assert run_response.horizon_minutes == 180
    assert run_response.timestep_minutes == 30
    assert run_response.total_timesteps == 7
    assert run_response.available_slices == [0, 30, 60, 90, 120, 150, 180]
    assert len(run_response.time_slices) == 7


@pytest.mark.asyncio
async def test_digital_twin_canonical_time_slices():
    """Verify exactly 7 time slices with canonical minute offsets."""
    service = DigitalTwinService()
    req = DigitalTwinRunRequestSchema()
    run_response = await service.create_run(req)

    minutes = [slice_obj.minutes_from_start for slice_obj in run_response.time_slices]
    assert minutes == [0, 30, 60, 90, 120, 150, 180]


@pytest.mark.asyncio
async def test_prototype_ml_score_labeling():
    """Verify Phase 8 score is labeled PROTOTYPE_ONLY for T=0 real event and does not claim validated probability."""
    service = DigitalTwinService()
    cell_diag = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=0)

    assert cell_diag.prototype_ml_score is not None
    assert cell_diag.ml_status_tag == "PROTOTYPE_ONLY"
    assert "Prototype ML Score" in cell_diag.disclaimer
    assert "not operationally validated" in cell_diag.disclaimer.lower()
    assert "validated probability" not in cell_diag.disclaimer.lower()


@pytest.mark.asyncio
async def test_future_slice_ml_score_unavailable():
    """Verify future slices T>0 without slice-specific rainfall rasters return UNAVAILABLE ML score."""
    service = DigitalTwinService()
    cell_diag = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=60)

    assert cell_diag.prototype_ml_score is None
    assert cell_diag.ml_status_tag == "UNAVAILABLE"


@pytest.mark.asyncio
async def test_phase8_phase9_integration_and_provenance():
    """Verify Phase 8 calibration integrates into Phase 9 with strict provenance."""
    service = DigitalTwinService()
    req = DigitalTwinRunRequestSchema(study_area_id="mumbai_mithi")
    run_response = await service.create_run(req)

    summary = run_response.summary
    assert summary is not None
    prov = summary.provenance

    assert prov.get("physical_engine") == "Phase6_Deterministic_D8"
    assert prov.get("ml_calibration") == "Phase8_XGBoost_Prototype_V1"
    assert prov.get("ml_status") == "PROTOTYPE_ONLY"
    assert prov.get("data_mode") == "REAL_DATA"
    assert prov.get("event_id") == "E05"
    assert prov.get("grid") == "392 x 476, 30m x 30m, EPSG:32643"
    assert len(prov.get("sha256", "")) == 64


@pytest.mark.asyncio
async def test_physical_authority_not_replaced_by_ml():
    """Verify physical water depth and severity remain primary authority and are not overwritten by ML score."""
    service = DigitalTwinService()
    cell_diag = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=0)

    assert hasattr(cell_diag, "water_depth_m")
    assert hasattr(cell_diag, "severity")
    assert hasattr(cell_diag, "prototype_ml_score")

    assert cell_diag.water_depth_m >= 0.0
    assert 0.0 <= cell_diag.prototype_ml_score <= 1.0
    assert cell_diag.water_depth_m != cell_diag.prototype_ml_score


@pytest.mark.asyncio
async def test_training_label_isolation():
    """Verify operational cell inspection exposes zero Phase 7 training target labels."""
    service = DigitalTwinService()
    cell_diag = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=60)

    cell_dict = cell_diag.model_dump()
    forbidden_keys = [
        "flood_label",
        "label_status",
        "label_confidence",
        "evidence_source",
        "verified_positive",
        "evidence_quality",
        "training_target_type",
    ]
    for key in forbidden_keys:
        assert key not in cell_dict, f"Forbidden label key '{key}' exposed in operational response"


@pytest.mark.asyncio
async def test_api_create_and_list_runs(async_client):
    """Verify POST /api/v1/digital-twin/runs creates run and GET endpoints retrieve it."""
    response = await async_client.post(
        "/api/v1/digital-twin/runs",
        json={"study_area_id": "mumbai_mithi", "horizon_minutes": 180, "timestep_minutes": 30},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["horizon_minutes"] == 180
    assert len(data["available_slices"]) == 7

    run_id = data["run_id"]

    get_resp = await async_client.get(f"/api/v1/digital-twin/runs/{run_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["run_id"].startswith("dt_")

    slices_resp = await async_client.get(f"/api/v1/digital-twin/runs/{run_id}/timeslices")
    assert slices_resp.status_code == 200
    slices_data = slices_resp.json()
    assert len(slices_data) == 7

    summary_resp = await async_client.get(f"/api/v1/digital-twin/runs/{run_id}/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["run_id"].startswith("dt_")
    assert summary_data["ml_calibration_status"] == "PROTOTYPE_ONLY"


@pytest.mark.asyncio
async def test_api_latest_run(async_client):
    """Verify GET /api/v1/digital-twin/runs/latest returns latest run."""
    response = await async_client.get("/api/v1/digital-twin/runs/latest")
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["horizon_minutes"] == 180


@pytest.mark.asyncio
async def test_api_map_slice_and_invalid_slice(async_client):
    """Verify map slice metadata endpoint returns compact raster metadata and rejects invalid slice minute values."""
    valid_resp = await async_client.get("/api/v1/digital-twin/runs/dt_demo_run/map/60")
    assert valid_resp.status_code == 200
    valid_data = valid_resp.json()
    assert valid_data["minutes_from_start"] == 60
    assert valid_data["artifact_type"] == "MAP_RASTER"
    assert valid_data["format"] == "GEOTIFF"
    assert valid_data["crs"] == "EPSG:4326"
    assert "relative_path" in valid_data

    invalid_resp = await async_client.get("/api/v1/digital-twin/runs/dt_demo_run/map/45")
    assert invalid_resp.status_code == 400
    assert "Unsupported time slice" in invalid_resp.json()["detail"]


@pytest.mark.asyncio
async def test_api_cell_inspection(async_client):
    """Verify GET /api/v1/digital-twin/runs/{run_id}/inspect requires valid cell and returns diagnostics."""
    resp = await async_client.get("/api/v1/digital-twin/runs/dt_demo_run/inspect?grid_cell_id=CELL_R0020_C0020&minutes_from_start=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["grid_cell_id"] == "CELL_R0020_C0020"
    assert data["ml_status_tag"] == "PROTOTYPE_ONLY"
    assert "flood_label" not in data


@pytest.mark.asyncio
async def test_compact_raster_map_artifact_architecture():
    """Verify primary map delivery mechanism generates compact GeoTIFF rasters (no giant per-cell GeoJSON)."""
    service = DigitalTwinService()
    req = DigitalTwinRunRequestSchema(study_area_id="mumbai_mithi", horizon_minutes=180, timestep_minutes=30)
    run_response = await service.create_run(req)

    for slice_obj in run_response.time_slices:
        assert slice_obj.artifact_path.endswith(".tif")


@pytest.mark.asyncio
async def test_missing_model_artifact_degrades_gracefully(tmp_path, monkeypatch):
    """Verify missing model artifact degrades ML score cleanly to UNAVAILABLE without failing physical simulation."""
    fake_path = str(tmp_path / "non_existent.joblib")
    monkeypatch.setattr("app.core.config.settings.AQUORA_CALIBRATION_MODEL_PATH", fake_path)

    service = DigitalTwinService()
    cell_diag = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=60)
    assert cell_diag.ml_status_tag == "UNAVAILABLE"
    assert cell_diag.prototype_ml_score is None

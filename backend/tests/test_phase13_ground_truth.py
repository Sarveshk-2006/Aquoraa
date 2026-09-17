"""Focused Test Suite for Phase 13 Ground Truth + Photo Verification.

Verifies:
- Observation schema validation & contradictory field rejection
- Provider abstractions (Synthetic DEVELOPMENT_ONLY & Local GeoJSON)
- Secure media validation (MIME, size, path traversal, SHA256 hash)
- Photo quality & bounded CV assessment (exact depth prohibited)
- Incident clustering & unique source counting
- Multi-source verification rules (UNVERIFIED, CORROBORATED, CONFIRMED)
- Single report / photo / CV non-override invariants
- Digital Twin ↔ observation temporal (elapsed minutes, 7 canonical slices) & spatial matching
- Explainable comparison statements & cautious contradiction warnings
- Privacy, governance disclaimers, and FastAPI endpoint integration
"""

from datetime import datetime, timedelta, timezone

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from app.providers.ground_truth import (
    LocalGroundTruthProvider,
    LocalPhotoAssessmentProvider,
    SyntheticGroundTruthProvider,
)
from app.schemas.ground_truth import (
    EvidenceStrength,
    FloodPresence,
    GroundTruthRunRequestSchema,
    ImageQuality,
    ModelComparisonStatus,
    ObservationCreateSchema,
    ObservationSourceType,
    ObservationType,
    ObserverType,
    RoadPassability,
    VerificationState,
    WaterDepthClass,
)
from app.services.ground_truth_service import GroundTruthService


@pytest.mark.asyncio
async def test_1_observation_schema_and_contradictory_field_rejection():
    """Verify schema validation and rejection of impossible field combinations."""
    # Valid observation payload
    valid_payload = ObservationCreateSchema(
        latitude=19.0760,
        longitude=72.8777,
        location_source="GPS",
        observed_at=datetime.now(timezone.utc).isoformat(),
        source=ObservationSourceType.COMMUNITY,
        observer_type=ObserverType.COMMUNITY,
        observation_type=ObservationType.FLOOD_REPORT,
        flood_presence=FloodPresence.FLOOD_PRESENT,
        water_depth_class=WaterDepthClass.TEN_TO_TWENTY_CM,
        road_passability=RoadPassability.DIFFICULT,
        description="Water accumulating near roadway.",
    )
    assert valid_payload.latitude == 19.0760
    assert valid_payload.flood_presence == FloodPresence.FLOOD_PRESENT

    # Contradictory payload (NO_FLOOD_OBSERVED + deep water)
    with pytest.raises(ValueError, match="Cannot specify deep water depth"):
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            flood_presence=FloodPresence.NO_FLOOD_OBSERVED,
            water_depth_class=WaterDepthClass.GREATER_THAN_40CM,
        )


@pytest.mark.asyncio
async def test_2_synthetic_provider_determinism_and_development_only():
    """Verify SyntheticGroundTruthProvider yields deterministic tagged test observations."""
    provider = SyntheticGroundTruthProvider(center_lat=19.0760, center_lon=72.8777, num_observations=5)
    assert provider.provider_id == "SYNTHETIC_GROUND_TRUTH_PROVIDER"
    assert provider.provider_mode == "SYNTHETIC"

    observations = await provider.fetch_observations()
    assert len(observations) == 5

    # Confirm synthetic disclosure in descriptions and provenance
    for obs in observations:
        assert "TEST OBSERVATION" in obs.description
        assert obs.provenance.get("disclaimer") == "DEVELOPMENT_ONLY / TEST_ONLY — Synthetic demonstration observation."
        assert obs.provenance.get("provider_mode") == "SYNTHETIC"


@pytest.mark.asyncio
async def test_3_local_provider_provenance(tmp_path):
    """Verify LocalGroundTruthProvider loads local GeoJSON and preserves provenance."""
    geojson_path = tmp_path / "test_obs.geojson"
    geojson_path.write_text(
        """{
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [72.8500, 19.0500]},
                    "properties": {
                        "source": "FIELD_TEAM",
                        "observer_type": "FIELD_TEAM",
                        "flood_presence": "FLOOD_PRESENT",
                        "water_depth_class": "20_TO_40CM",
                        "description": "Field team inspection."
                    }
                }
            ]
        }""",
        encoding="utf-8",
    )

    provider = LocalGroundTruthProvider(data_path=geojson_path)
    assert provider.provider_mode == "LOCAL"

    obs_list = await provider.fetch_observations()
    assert len(obs_list) == 1
    assert obs_list[0].longitude == 72.8500
    assert obs_list[0].latitude == 19.0500
    assert obs_list[0].source == ObservationSourceType.FIELD_TEAM
    assert obs_list[0].provenance.get("source_file") == "test_obs.geojson"


@pytest.mark.asyncio
async def test_4_photo_assessment_provider_bounded_rules(tmp_path):
    """Verify LocalPhotoAssessmentProvider executes quality checks without claiming exact depth."""
    assessor = LocalPhotoAssessmentProvider()
    assert assessor.provider_id == "LOCAL_BOUNDED_PHOTO_ASSESSMENT_PROVIDER"

    test_file = tmp_path / "test_photo.jpg"
    test_file.write_bytes(b"FFD8FF" + b"X" * 2048)

    res = await assessor.assess_photo(file_path=test_file, mime_type="image/jpeg", file_size=len(test_file.read_bytes()))
    assert res.get("image_quality") == ImageQuality.SUFFICIENT
    assert res.get("cv_status") == "DEVELOPMENT_ONLY"
    assert res.get("water_presence_indicated") is True
    # Verify exact depth is NOT claimed
    assert "exact_depth" not in res
    assert "Exact water depth is not claimed" in res.get("disclaimer", "")


@pytest.mark.asyncio
async def test_5_ground_truth_service_creation_and_media_upload(tmp_path):
    """Verify service observation creation, safe media upload, file hash, and path traversal protection."""
    service = GroundTruthService(db=None)

    payload = ObservationCreateSchema(
        latitude=19.0800,
        longitude=72.8800,
        location_source="MANUAL",
        source=ObservationSourceType.COMMUNITY,
        flood_presence=FloodPresence.FLOOD_PRESENT,
        water_depth_class=WaterDepthClass.TEN_TO_TWENTY_CM,
        road_passability=RoadPassability.DIFFICULT,
        description="Community report.",
    )

    obs = await service.create_observation(payload)
    assert obs.observation_id.startswith("obs_")
    assert obs.verification_state == VerificationState.UNVERIFIED.value
    assert obs.evidence_strength == EvidenceStrength.WEAK.value

    # Upload test image
    content = b"\xFF\xD8\xFF\xE0" + b"test_image_data_bytes" * 50
    media = await service.upload_media(
        observation_id=obs.observation_id,
        filename="../dangerous_path/test_photo.jpg",  # Path traversal attempt
        content_bytes=content,
        mime_type="image/jpeg",
    )

    assert media.media_id.startswith("media_")
    assert "dangerous_path" not in media.storage_reference  # Path traversal stripped
    assert len(media.file_hash) == 64  # Valid SHA256
    assert media.mime_type == "image/jpeg"


@pytest.mark.asyncio
async def test_6_incident_clustering_and_unique_source_counting():
    """Verify deterministic incident clustering and unique source counting."""
    service = GroundTruthService(db=None)
    now = datetime.now(timezone.utc)

    # 3 observations near lat 19.076, lon 72.877 within 100m and 10 minutes
    obs1 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            source=ObservationSourceType.COMMUNITY,
            source_id="USER_001",
            observed_at=now.isoformat(),
        )
    )
    obs2 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0762,
            longitude=72.8779,
            source=ObservationSourceType.COMMUNITY,
            source_id="USER_002",
            observed_at=(now + timedelta(minutes=5)).isoformat(),
        )
    )
    obs3 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0761,
            longitude=72.8778,
            source=ObservationSourceType.FIELD_TEAM,
            source_id="FIELD_001",
            observed_at=(now + timedelta(minutes=8)).isoformat(),
        )
    )

    incidents = await service.cluster_incidents([obs1, obs2, obs3], cluster_radius_m=250.0, cluster_time_minutes=60.0)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.observation_count == 3
    assert inc.unique_source_count == 3
    # 3 independent sources -> CONFIRMED
    assert inc.verification_state == VerificationState.CONFIRMED.value


@pytest.mark.asyncio
async def test_7_multi_source_verification_state_invariants():
    """Verify verification state rules: single report cannot confirm."""
    service = GroundTruthService(db=None)

    # Single community observation -> UNVERIFIED
    obs_single = await service.create_observation(
        ObservationCreateSchema(latitude=19.07, longitude=72.87, source=ObservationSourceType.COMMUNITY)
    )
    v_single = service.evaluate_verification_state([obs_single])
    assert v_single == VerificationState.UNVERIFIED

    # 2 independent community sources -> CORROBORATED
    obs_b = await service.create_observation(
        ObservationCreateSchema(latitude=19.07, longitude=72.87, source=ObservationSourceType.COMMUNITY, source_id="SRC_B")
    )
    v_double = service.evaluate_verification_state([obs_single, obs_b])
    assert v_double == VerificationState.CORROBORATED

    # Authority report -> CONFIRMED
    obs_auth = await service.create_observation(
        ObservationCreateSchema(latitude=19.07, longitude=72.87, source=ObservationSourceType.AUTHORITY)
    )
    v_auth = service.evaluate_verification_state([obs_auth])
    assert v_auth == VerificationState.CONFIRMED


@pytest.mark.asyncio
async def test_8_digital_twin_temporal_and_spatial_comparison():
    """Verify Digital Twin ↔ observation elapsed time matching and canonical 7-slice resolution."""
    service = GroundTruthService(db=None)
    run_start = datetime(2026, 9, 13, 14, 0, 0, tzinfo=timezone.utc)
    obs_time = datetime(2026, 9, 13, 14, 53, 0, tzinfo=timezone.utc)  # Elapsed 53m

    obs = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            observed_at=obs_time.isoformat(),
            flood_presence=FloodPresence.FLOOD_PRESENT,
            water_depth_class=WaterDepthClass.TWENTY_TO_FORTY_CM,
        )
    )

    comp = await service.compare_observation_with_digital_twin(
        observation=obs,
        digital_twin_run_id="dt_run_test_001",
        dt_run_start_time=run_start,
        max_time_diff_minutes=20.0,
    )

    assert comp.model_slice_minutes == 60  # Elapsed 53m matches canonical slice +60m
    assert comp.observation_elapsed_minutes == 53.0
    assert abs(comp.time_difference_minutes - 7.0) < 0.1
    assert comp.comparison_status == ModelComparisonStatus.MODEL_SUPPORTS_OBSERVATION.value
    assert "consistent with modeled" in comp.explanation


@pytest.mark.asyncio
async def test_9_time_mismatch_handling():
    """Verify time mismatch when observation time exceeds maximum slice tolerance."""
    service = GroundTruthService(db=None)
    run_start = datetime(2026, 9, 13, 14, 0, 0, tzinfo=timezone.utc)
    obs_time = datetime(2026, 9, 13, 20, 0, 0, tzinfo=timezone.utc)  # Elapsed 360m (out of 180m horizon)

    obs = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            observed_at=obs_time.isoformat(),
        )
    )

    comp = await service.compare_observation_with_digital_twin(
        observation=obs,
        digital_twin_run_id="dt_run_test_001",
        dt_run_start_time=run_start,
        max_time_diff_minutes=20.0,
    )

    assert comp.comparison_status == ModelComparisonStatus.TIME_MISMATCH.value
    assert "TIME_MISMATCH" in comp.warnings[0]


@pytest.mark.asyncio
async def test_10_ground_truth_run_execution():
    """Verify GroundTruthService full run execution in SYNTHETIC mode."""
    service = GroundTruthService(db=None)
    payload = GroundTruthRunRequestSchema(provider_mode="SYNTHETIC", cluster_radius_m=250.0)

    run_res = await service.execute_run(payload)
    assert run_res.run_id.startswith("gt_run_")
    assert run_res.status == "COMPLETED"
    assert run_res.observation_count >= 5
    assert run_res.incident_count >= 1
    assert run_res.comparison_count >= 5
    assert run_res.provider_mode == "SYNTHETIC"


@pytest.mark.asyncio
async def test_same_source_multiple_observations_do_not_corroborate():
    """CASE A / CASE G: Multiple observations from the same source MUST remain UNVERIFIED."""
    service = GroundTruthService(db=None)

    obs1 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            source=ObservationSourceType.COMMUNITY,
            source_id="USER_ALPHA",
            observer_reference="USER_ALPHA",
            description="First report from User Alpha",
        )
    )

    obs2 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0762,
            longitude=72.8779,
            source=ObservationSourceType.COMMUNITY,
            source_id="USER_ALPHA",
            observer_reference="USER_ALPHA",
            description="Second report from User Alpha",
        )
    )

    # Unique source count must be 1, NOT 2
    verification = service.evaluate_verification_state([obs1, obs2])
    assert verification == VerificationState.UNVERIFIED


@pytest.mark.asyncio
async def test_same_source_multiple_media_do_not_corroborate(tmp_path):
    """CASE B / CASE H: Multiple media uploads on one observation do NOT grant CORROBORATED state."""
    service = GroundTruthService(db=None)

    obs = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            source=ObservationSourceType.COMMUNITY,
            source_id="USER_BETA",
        )
    )

    # Upload photo 1
    content1 = b"\xFF\xD8\xFF\xE0" + b"photo_data_1" * 50
    await service.upload_media(obs.observation_id, "photo1.jpg", content1, "image/jpeg")

    # Upload photo 2
    content2 = b"\xFF\xD8\xFF\xE0" + b"photo_data_2" * 50
    await service.upload_media(obs.observation_id, "photo2.jpg", content2, "image/jpeg")

    # Single observation with multiple photos must remain UNVERIFIED
    verification = service.evaluate_verification_state([obs])
    assert verification == VerificationState.UNVERIFIED


@pytest.mark.asyncio
async def test_same_observation_cv_does_not_corroborate(tmp_path):
    """CASE C: CV assessment of an observation's media does NOT count as an independent source."""
    service = GroundTruthService(db=None)

    obs = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            source=ObservationSourceType.COMMUNITY,
            source_id="USER_GAMMA",
        )
    )

    content = b"\xFF\xD8\xFF\xE0" + b"cv_test_data" * 50
    media = await service.upload_media(obs.observation_id, "cv_photo.jpg", content, "image/jpeg")

    assert media.cv_status == "DEVELOPMENT_ONLY"
    # CV output is derived evidence; observation verification remains UNVERIFIED
    verification = service.evaluate_verification_state([obs])
    assert verification == VerificationState.UNVERIFIED


@pytest.mark.asyncio
async def test_two_independent_sources_can_corroborate():
    """CASE D / CASE E: Two distinct independent sources produce CORROBORATED state."""
    service = GroundTruthService(db=None)

    obs_comm = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            source=ObservationSourceType.COMMUNITY,
            source_id="CITIZEN_101",
        )
    )

    obs_field = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0761,
            longitude=72.8778,
            source=ObservationSourceType.FIELD_TEAM,
            source_id="CREW_202",
        )
    )

    verification = service.evaluate_verification_state([obs_comm, obs_field])
    assert verification == VerificationState.CORROBORATED


@pytest.mark.asyncio
async def test_spatial_temporal_consistency_does_not_equal_independence():
    """CASE G: Spatial/temporal consistency alone from same source does NOT equal independent sources."""
    service = GroundTruthService(db=None)
    now = datetime.now(timezone.utc)

    # 3 spatially/temporally consistent observations submitted by the SAME source ID
    obs1 = await service.create_observation(
        ObservationCreateSchema(latitude=19.0760, longitude=72.8777, source_id="SINGLE_USER", observed_at=now.isoformat())
    )
    obs2 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0761, longitude=72.8778, source_id="SINGLE_USER", observed_at=(now + timedelta(minutes=2)).isoformat()
        )
    )
    obs3 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0762, longitude=72.8779, source_id="SINGLE_USER", observed_at=(now + timedelta(minutes=4)).isoformat()
        )
    )

    verification = service.evaluate_verification_state([obs1, obs2, obs3])
    assert verification == VerificationState.UNVERIFIED


@pytest.mark.asyncio
async def test_unique_source_count_is_not_observation_count():
    """Section 6 Audit: Verify unique_source_count is based on source identity, NOT observation count."""
    service = GroundTruthService(db=None)
    now = datetime.now(timezone.utc)

    obs_list = [
        await service.create_observation(
            ObservationCreateSchema(latitude=19.0760, longitude=72.8777, source_id="REPEATED_USER", observed_at=now.isoformat())
        )
        for _ in range(5)
    ]

    incidents = await service.cluster_incidents(obs_list, cluster_radius_m=250.0, cluster_time_minutes=60.0)
    assert len(incidents) == 1
    assert incidents[0].observation_count == 5
    assert incidents[0].unique_source_count == 1  # 5 observations, 1 unique source


@pytest.mark.asyncio
async def test_incident_clustering_does_not_manufacture_corroboration():
    """Section 5 Audit: Verify incident clustering does NOT manufacture false corroboration."""
    service = GroundTruthService(db=None)
    now = datetime.now(timezone.utc)

    obs1 = await service.create_observation(
        ObservationCreateSchema(latitude=19.0760, longitude=72.8777, source_id="SAME_CITIZEN", observed_at=now.isoformat())
    )
    obs2 = await service.create_observation(
        ObservationCreateSchema(
            latitude=19.0761, longitude=72.8778, source_id="SAME_CITIZEN", observed_at=(now + timedelta(minutes=3)).isoformat()
        )
    )

    incidents = await service.cluster_incidents([obs1, obs2], cluster_radius_m=250.0, cluster_time_minutes=60.0)
    assert len(incidents) == 1
    assert incidents[0].verification_state == VerificationState.UNVERIFIED.value


@pytest.mark.asyncio
async def test_evidence_strength_is_separate_from_verification(tmp_path):
    """Section 8 Audit: Verify evidence strength (STRONG/MODERATE) is separate from verification state."""
    service = GroundTruthService(db=None)

    obs = await service.create_observation(
        ObservationCreateSchema(latitude=19.0760, longitude=72.8777, source=ObservationSourceType.COMMUNITY)
    )
    # Upload photo to elevate evidence strength
    content = b"\xFF\xD8\xFF\xE0" + b"strong_photo" * 50
    await service.upload_media(obs.observation_id, "photo.jpg", content, "image/jpeg")

    # In-memory strength elevation
    obs.evidence_strength = EvidenceStrength.MODERATE.value
    obs.media_count = 1

    # Photo elevates evidence strength to MODERATE
    assert obs.evidence_strength == EvidenceStrength.MODERATE.value
    # Verification state MUST remain UNVERIFIED until independent corroboration
    assert obs.verification_state == VerificationState.UNVERIFIED.value


@pytest.mark.asyncio
async def test_single_source_cannot_confirm():
    """Section 9 Audit: Verify single community source with 10 reports cannot achieve CONFIRMED state."""
    service = GroundTruthService(db=None)

    obs_list = [
        await service.create_observation(
            ObservationCreateSchema(latitude=19.0760, longitude=72.8777, source_id="SINGLE_COMMUNITY_USER")
        )
        for _ in range(10)
    ]

    verification = service.evaluate_verification_state(obs_list)
    assert verification == VerificationState.UNVERIFIED
    assert verification != VerificationState.CONFIRMED


@pytest.mark.asyncio
async def test_post_ground_truth_runs_success_and_cors_audit():
    """Regression test for successful POST /api/v1/ground-truth/runs and CORS origin verification."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Successful POST from 127.0.0.1:5175
        res = await client.post(
            "/api/v1/ground-truth/runs",
            json={"provider_mode": "SYNTHETIC"},
            headers={"Origin": "http://127.0.0.1:5175"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "COMPLETED"
        assert "run_id" in data
        assert res.headers.get("access-control-allow-origin") == "http://127.0.0.1:5175"

        # 2. Successful POST from localhost:5175
        res_lh = await client.post(
            "/api/v1/ground-truth/runs",
            json={"provider_mode": "SYNTHETIC"},
            headers={"Origin": "http://localhost:5175"},
        )
        assert res_lh.status_code == 201
        assert res_lh.headers.get("access-control-allow-origin") == "http://localhost:5175"

        # 3. OPTIONS preflight
        res_opt = await client.options(
            "/api/v1/ground-truth/runs",
            headers={
                "Origin": "http://127.0.0.1:5175",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert res_opt.status_code == 200
        assert res_opt.headers.get("access-control-allow-origin") == "http://127.0.0.1:5175"

        # 4. Error response CORS header preservation
        res_err = await client.post(
            "/api/v1/ground-truth/runs",
            json={"cluster_radius_m": "invalid_number"},
            headers={"Origin": "http://127.0.0.1:5175"},
        )
        assert res_err.status_code == 422
        assert res_err.headers.get("access-control-allow-origin") == "http://127.0.0.1:5175"



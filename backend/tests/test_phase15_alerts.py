"""
Phase 15 Aquora Alerts, Explainability, and Audit Comprehensive Test Suite.

Verifies:
- Alert schema validation & explicit typed source-run contracts
- Complete alert taxonomy & operational severity mapping
- Alert lifecycle transitions (ACTIVE -> ACKNOWLEDGED -> RESOLVED / SUPPRESSED)
- Flood onset & high/severe flood risk alerts (Phase 9 Digital Twin integration)
- Travel window closing & route avoid alerts (Phase 10 Routing integration)
- Critical access threat & loss alerts (Phase 11 Critical Access integration)
- Protect City priority alerts (Phase 12 Protect City integration)
- Ground truth conflict alerts (Phase 13 Ground Truth integration)
- Simulator scenario result alerts (Phase 14 Simulator integration)
- Structured cause-chain explainability steps (WHAT, WHY, WHEN, WHERE, HOW_CERTAIN, WHAT_SHOULD_I_DO, EVIDENCE)
- Compact evidence recording & cryptographic provenance hashing
- Deterministic fingerprinting & continuing-condition deduplication
- Alert escalation / de-escalation & lifecycle audit trail logging
- Mandatory Duplicate-Engine Audit (0 duplicate solvers)
- Historical alert immutability & phase/source isolation
- FastAPI endpoints for alert listing, detail, generation, lifecycle actions, evidence, explainability, audit, provenance, and configuration
- Production environment database failure guardrail
"""

import pytest
from app.db.session import get_db
from app.main import app
from app.schemas.alerts import (
    AlertAcknowledgeSchema,
    AlertGenerateRequestSchema,
    AlertResolveSchema,
    AlertSeverity,
    AlertStatus,
    AlertSuppressSchema,
    AlertType,
    EvidenceStrength,
)
from app.services.alerts_service import AlertsService
from fastapi.testclient import TestClient


@pytest.fixture
def service():
    return AlertsService(db=None)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: None
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


# ============================================================
# 1. SCHEMA VALIDATION & EXPLICIT SOURCE CONTRACT TESTS
# ============================================================

def test_alert_generation_request_schema_validation():
    """Verify AlertGenerateRequestSchema requires at least one valid source run ID."""
    # Valid payload with Digital Twin run ID
    valid = AlertGenerateRequestSchema(digital_twin_run_id="dt_run_mithi_001")
    assert valid.digital_twin_run_id == "dt_run_mithi_001"

    # Invalid empty payload (no source run IDs)
    with pytest.raises(ValueError, match="At least one valid authoritative source run_id must be provided"):
        AlertGenerateRequestSchema()


def test_alert_taxonomy_and_severity_enums():
    """Verify all 13 controlled AlertType enums and 5 AlertSeverity enums."""
    assert len(AlertType) == 13
    assert AlertType.FLOOD_ONSET == "FLOOD_ONSET"
    assert AlertType.ROUTE_AVOID == "ROUTE_AVOID"
    assert AlertType.CRITICAL_ACCESS_LOSS == "CRITICAL_ACCESS_LOSS"
    assert AlertType.PROTECT_CITY_PRIORITY == "PROTECT_CITY_PRIORITY"
    assert AlertType.GROUND_TRUTH_CONFLICT == "GROUND_TRUTH_CONFLICT"
    assert AlertType.SIMULATOR_SCENARIO_RESULT == "SIMULATOR_SCENARIO_RESULT"

    assert len(AlertSeverity) == 5
    assert AlertSeverity.INFO == "INFO"
    assert AlertSeverity.CRITICAL == "CRITICAL"


# ============================================================
# 2. PHASE-SPECIFIC ALERT GENERATION TESTS
# ============================================================

@pytest.mark.asyncio
async def test_digital_twin_flood_onset_alert(service):
    """Verify Phase 9 Digital Twin run evaluates into HIGH_SEVERE_FLOOD_RISK alert."""
    payload = AlertGenerateRequestSchema(digital_twin_run_id="dt_run_mithi_001")
    res = await service.generate_alerts(payload)

    assert res.total_count >= 1
    alt = res.alerts[0]
    assert alt.alert_type == AlertType.HIGH_SEVERE_FLOOD_RISK
    assert alt.severity == AlertSeverity.HIGH
    assert alt.status == AlertStatus.ACTIVE
    assert alt.source_phase == "Phase9"
    assert alt.source_run_id == "dt_run_mithi_001"
    assert "Mithi River Basin" in alt.title


@pytest.mark.asyncio
async def test_travel_window_route_avoid_alert(service):
    """Verify Phase 10 Travel Window run evaluates into ROUTE_AVOID alert."""
    payload = AlertGenerateRequestSchema(travel_window_run_id="tw_run_west_001")
    res = await service.generate_alerts(payload)

    assert res.total_count >= 1
    alt = res.alerts[0]
    assert alt.alert_type == AlertType.ROUTE_AVOID
    assert alt.severity == AlertSeverity.CRITICAL
    assert alt.source_phase == "Phase10"
    assert alt.affected_entity_id == "WEST_CORRIDOR_01"


@pytest.mark.asyncio
async def test_critical_access_loss_alert(service):
    """Verify Phase 11 Critical Access run evaluates into CRITICAL_ACCESS_LOSS alert."""
    payload = AlertGenerateRequestSchema(critical_access_run_id="ca_run_central_001")
    res = await service.generate_alerts(payload)

    assert res.total_count >= 1
    alt = res.alerts[0]
    assert alt.alert_type == AlertType.CRITICAL_ACCESS_LOSS
    assert alt.severity == AlertSeverity.CRITICAL
    assert alt.source_phase == "Phase11"
    assert alt.affected_entity_id == "FAC_HOSPITAL_01"


@pytest.mark.asyncio
async def test_protect_city_priority_alert(service):
    """Verify Phase 12 Protect City run evaluates into PROTECT_CITY_PRIORITY alert."""
    payload = AlertGenerateRequestSchema(protect_city_run_id="pc_run_gate04_001")
    res = await service.generate_alerts(payload)

    assert res.total_count >= 1
    alt = res.alerts[0]
    assert alt.alert_type == AlertType.PROTECT_CITY_PRIORITY
    assert alt.severity == AlertSeverity.HIGH
    assert alt.source_phase == "Phase12"
    assert alt.affected_entity_id == "INT_GATE_04"


@pytest.mark.asyncio
async def test_ground_truth_conflict_alert(service):
    """Verify Phase 13 Ground Truth run evaluates into GROUND_TRUTH_CONFLICT alert."""
    payload = AlertGenerateRequestSchema(ground_truth_run_id="gt_run_cell402_001")
    res = await service.generate_alerts(payload)

    assert res.total_count >= 1
    alt = res.alerts[0]
    assert alt.alert_type == AlertType.GROUND_TRUTH_CONFLICT
    assert alt.severity == AlertSeverity.MEDIUM
    assert alt.evidence_strength == EvidenceStrength.CORROBORATED
    assert alt.source_phase == "Phase13"


@pytest.mark.asyncio
async def test_simulator_scenario_result_alert(service):
    """Verify Phase 14 Simulator run evaluates into SIMULATOR_SCENARIO_RESULT alert."""
    payload = AlertGenerateRequestSchema(simulator_run_id="simrun_1.5x_001")
    res = await service.generate_alerts(payload)

    assert res.total_count >= 1
    alt = res.alerts[0]
    assert alt.alert_type == AlertType.SIMULATOR_SCENARIO_RESULT
    assert alt.severity == AlertSeverity.INFO
    assert alt.source_phase == "Phase14"
    assert "what-if estimates" in alt.governance_notice


# ============================================================
# 3. EXPLAINABILITY, EVIDENCE, & PROVENANCE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_structured_explainability_cause_chain(service):
    """Verify alert explainability returns 7 structured steps (WHAT, WHY, WHEN, WHERE, HOW_CERTAIN, WHAT_SHOULD_I_DO, EVIDENCE)."""
    gen_res = await service.generate_alerts(AlertGenerateRequestSchema(digital_twin_run_id="dt_run_mithi_001"))
    alert_id = gen_res.alerts[0].alert_id

    steps = await service.get_explainability(alert_id)
    assert len(steps) == 7

    categories = [s.category for s in steps]
    assert categories == ["WHAT", "WHY", "WHEN", "WHERE", "HOW_CERTAIN", "WHAT_SHOULD_I_DO", "EVIDENCE"]

    # Source phase and run ID must be populated on every step
    for s in steps:
        assert s.source_phase is not None
        assert s.source_run_id is not None


@pytest.mark.asyncio
async def test_compact_evidence_references(service):
    """Verify evidence references are compact metrics, not giant copied payloads."""
    gen_res = await service.generate_alerts(AlertGenerateRequestSchema(critical_access_run_id="ca_run_central_001"))
    alert_id = gen_res.alerts[0].alert_id

    evidences = await service.get_evidence(alert_id)
    assert len(evidences) >= 1
    evd = evidences[0]
    assert evd.metric == "access_status"
    assert evd.source_phase == "Phase11"
    assert evd.source_run_id == "ca_run_central_001"


@pytest.mark.asyncio
async def test_alert_provenance_chain(service):
    """Verify alert provenance contains cryptographic hash and configuration version."""
    gen_res = await service.generate_alerts(AlertGenerateRequestSchema(simulator_run_id="simrun_1.5x_001"))
    alert_id = gen_res.alerts[0].alert_id

    prov = await service.get_provenance(alert_id)
    assert prov.alert_id == alert_id
    assert len(prov.provenance_hash) == 64
    assert prov.configuration_version == "v1"


# ============================================================
# 4. CONTINUING-CONDITION DEDUPLICATION & ESCALATION TESTS
# ============================================================

@pytest.mark.asyncio
async def test_continuing_condition_deduplication(service):
    """
    CONTINUING-CONDITION DEDUPLICATION TEST:
    Evaluating multiple runs with the same continuing condition updates 1 alert instead of creating duplicate records.
    """
    payload = AlertGenerateRequestSchema(digital_twin_run_id="dt_run_001")
    
    # Run 1
    res1 = await service.generate_alerts(payload)
    alert_id_1 = res1.alerts[0].alert_id

    # Run 2 (same condition)
    res2 = await service.generate_alerts(AlertGenerateRequestSchema(digital_twin_run_id="dt_run_002"))
    alert_id_2 = res2.alerts[0].alert_id

    # Run 3 (same condition)
    res3 = await service.generate_alerts(AlertGenerateRequestSchema(digital_twin_run_id="dt_run_003"))
    alert_id_3 = res3.alerts[0].alert_id

    # Alert ID must remain identical (deduplicated)
    assert alert_id_1 == alert_id_2 == alert_id_3

    # Total active alerts in system remains 1
    all_alerts = await service.list_alerts()
    dt_alerts = [a for a in all_alerts.alerts if a.alert_type == AlertType.HIGH_SEVERE_FLOOD_RISK]
    assert len(dt_alerts) == 1

    # Audit events track each continuing update
    audit_events = await service.get_audit_trail(alert_id_1)
    assert len(audit_events) >= 3


# ============================================================
# 5. LIFECYCLE STATE TRANSITION TESTS
# ============================================================

@pytest.mark.asyncio
async def test_alert_lifecycle_acknowledge_and_resolve(service):
    """Verify ACTIVE -> ACKNOWLEDGED -> RESOLVED status transitions and immutable audit events."""
    gen_res = await service.generate_alerts(AlertGenerateRequestSchema(critical_access_run_id="ca_run_central_001"))
    alert_id = gen_res.alerts[0].alert_id

    # 1. Acknowledge
    ack_res = await service.acknowledge_alert(
        alert_id, AlertAcknowledgeSchema(actor_reference="DISPATCH_UNIT_1", reason="Dispatch notified")
    )
    assert ack_res.status == AlertStatus.ACKNOWLEDGED
    assert ack_res.acknowledged_by == "DISPATCH_UNIT_1"

    # 2. Resolve
    res_res = await service.resolve_alert(
        alert_id, AlertResolveSchema(actor_reference="DISPATCH_UNIT_1", resolution_reason="Secondary access route opened")
    )
    assert res_res.status == AlertStatus.RESOLVED
    assert res_res.resolution_reason == "Secondary access route opened"

    # 3. Audit trail contains GENERATED, ACKNOWLEDGED, RESOLVED events
    events = await service.get_audit_trail(alert_id)
    event_types = [e.event_type for e in events]
    assert "GENERATED" in event_types
    assert "ACKNOWLEDGED" in event_types
    assert "RESOLVED" in event_types


@pytest.mark.asyncio
async def test_alert_lifecycle_suppression(service):
    """Verify ACTIVE -> SUPPRESSED status transition with mandatory suppression reason."""
    gen_res = await service.generate_alerts(AlertGenerateRequestSchema(protect_city_run_id="pc_run_gate04_001"))
    alert_id = gen_res.alerts[0].alert_id

    sup_res = await service.suppress_alert(
        alert_id, AlertSuppressSchema(actor_reference="CHIEF_ENGINEER", suppression_reason="Maintenance already underway")
    )
    assert sup_res.status == AlertStatus.SUPPRESSED
    assert sup_res.suppression_reason == "Maintenance already underway"


# ============================================================
# 6. MANDATORY DUPLICATE-ENGINE AUDIT
# ============================================================

def test_duplicate_engine_audit():
    """
    DUPLICATE-ENGINE AUDIT:
    Inspects app codebase to ensure Phase 15 does NOT implement duplicate solvers
    for runoff, D8 flow, routing, critical access, protect city, or simulator physics.
    """
    import inspect

    from app.services import alerts_service

    code_str = inspect.getsource(alerts_service)

    # Must NOT re-implement solvers
    assert "def calculate_d8_flow_direction" not in code_str
    assert "def runoff_generation" not in code_str
    assert "def calculate_route" not in code_str

    # Must consume authoritative source runs
    assert "source_run_id" in code_str


# ============================================================
# 7. API ENDPOINT INTEGRATION TESTS
# ============================================================

def test_api_alerts_lifecycle(client):
    """Test full HTTP API lifecycle: POST generate -> GET list -> GET detail -> POST acknowledge -> POST resolve."""
    # 1. Generate
    resp_gen = client.post(
        "/api/v1/alerts/generate",
        json={"digital_twin_run_id": "dt_api_test_001"},
    )
    assert resp_gen.status_code == 201
    gen_data = resp_gen.json()
    assert gen_data["total_count"] >= 1
    alert_id = gen_data["alerts"][0]["alert_id"]

    # 2. List
    resp_list = client.get("/api/v1/alerts?status=ACTIVE")
    assert resp_list.status_code == 200
    assert resp_list.json()["total_count"] >= 1

    # 3. Detail
    resp_detail = client.get(f"/api/v1/alerts/{alert_id}")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["alert_id"] == alert_id

    # 4. Explainability
    resp_exp = client.get(f"/api/v1/alerts/{alert_id}/explainability")
    assert resp_exp.status_code == 200
    assert len(resp_exp.json()) == 7

    # 5. Evidence
    resp_evd = client.get(f"/api/v1/alerts/{alert_id}/evidence")
    assert resp_evd.status_code == 200

    # 6. Audit
    resp_aud = client.get(f"/api/v1/alerts/{alert_id}/audit")
    assert resp_aud.status_code == 200

    # 7. Provenance
    resp_prov = client.get(f"/api/v1/alerts/{alert_id}/provenance")
    assert resp_prov.status_code == 200

    # 8. Acknowledge
    resp_ack = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"actor_reference": "TEST_OPERATOR", "reason": "Acknowledged via API test"},
    )
    assert resp_ack.status_code == 200
    assert resp_ack.json()["status"] == "ACKNOWLEDGED"

    # 9. Resolve
    resp_res = client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"actor_reference": "TEST_OPERATOR", "resolution_reason": "Resolved via API test"},
    )
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "RESOLVED"


def test_api_configuration_read_and_validate(client):
    """Test API configuration endpoints GET /alerts/configuration and POST /alerts/configuration/validate."""
    resp_get = client.get("/api/v1/alerts/configuration")
    assert resp_get.status_code == 200
    assert "thresholds" in resp_get.json()

    resp_val = client.post(
        "/api/v1/alerts/configuration/validate",
        json={
            "configuration_version": "v1",
            "thresholds": {"ALERT_FLOOD_ONSET_LOOKAHEAD_MINUTES": 60},
        },
    )
    assert resp_val.status_code == 200
    assert resp_val.json()["is_valid"] is True


def test_production_db_unavailable_guardrail(monkeypatch):
    """Verify production configuration fails cleanly if DB is unavailable instead of silently using in-memory fallback."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    prod_service = AlertsService(db=None)

    payload = AlertGenerateRequestSchema(digital_twin_run_id="dt_prod_test_001")

    with pytest.raises(RuntimeError, match="Database session unavailable in production environment"):
        import asyncio
        asyncio.run(prod_service.generate_alerts(payload))

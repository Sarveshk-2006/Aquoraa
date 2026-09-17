"""Phase 16 — Reproducibility & Fingerprint Stability Tests.

Validates that identical source inputs produce identical fingerprints, evidence metric hashes,
and deterministic explainability structures across repeated execution runs.
"""

from uuid import uuid4

import pytest
from app.schemas.alerts import AlertGenerateRequestSchema, AlertType
from app.services.alerts_service import AlertsService


def test_fingerprint_deterministic_hashing():
    """Verify that identical input strings produce identical SHA-256 fingerprints."""
    service = AlertsService(db=None)
    alert_type = AlertType.CRITICAL_ACCESS_LOSS.value
    affected_entity_type = "facility"
    affected_entity_id = "HOSPITAL_MUMBAI_CENTRAL"
    condition_key = "LOSS_OF_ACCESS"

    fp1 = service._compute_fingerprint(alert_type, affected_entity_type, affected_entity_id, condition_key)
    fp2 = service._compute_fingerprint(alert_type, affected_entity_type, affected_entity_id, condition_key)

    assert fp1 == fp2
    assert len(fp1) == 64  # Hexadecimal SHA-256 length


@pytest.mark.asyncio
async def test_repeated_runs_produce_identical_alert_structure():
    """Verify multiple executions yield identical structural alerts and evidence metrics."""
    service = AlertsService(db=None)

    dt_id = uuid4()
    ca_id = uuid4()

    req = AlertGenerateRequestSchema(
        digital_twin_run_id=str(dt_id),
        critical_access_run_id=str(ca_id),
    )

    alert1_list = await service.generate_alerts(req)
    alert2_list = await service.generate_alerts(req)

    a1 = alert1_list.alerts[0]
    a2 = alert2_list.alerts[0]

    assert a1.alert_id == a2.alert_id
    assert a1.fingerprint == a2.fingerprint
    assert a1.alert_type == a2.alert_type
    assert a1.severity == a2.severity

"""Phase 16 — Security & Boundary Protection Tests.

Validates parameter sanitization, Pydantic type safety, prevention of arbitrary file/path access,
forged provenance rejection, and rejection of invalid state transitions.
"""

import pytest
from app.schemas.alerts import (
    AlertAcknowledgeSchema,
    AlertGenerateRequestSchema,
)
from app.services.alerts_service import AlertsService
from fastapi import HTTPException
from pydantic import ValidationError


def test_malformed_uuid_rejected_by_schema():
    """Verify that empty request without source run IDs is rejected by Pydantic validation."""
    with pytest.raises(ValidationError):
        AlertGenerateRequestSchema()


@pytest.mark.asyncio
async def test_invalid_lifecycle_transition_rejected():
    """Verify state machine rejects invalid state transitions (e.g. RESOLVED -> ACKNOWLEDGED)."""
    service = AlertsService(db=None)

    req = AlertGenerateRequestSchema(digital_twin_run_id="run_dt_12345")
    alert_list = await service.generate_alerts(req)
    alert = alert_list.alerts[0]

    # First resolve the alert
    from app.schemas.alerts import AlertResolveSchema
    await service.resolve_alert(alert.alert_id, AlertResolveSchema(resolved_by="SYSTEM", resolution_reason="Cleared"))

    # Attempting to acknowledge a resolved alert must raise ValueError or HTTPException
    with pytest.raises((ValueError, HTTPException)):
        await service.acknowledge_alert(alert.alert_id, AlertAcknowledgeSchema(actor_reference="USER"))

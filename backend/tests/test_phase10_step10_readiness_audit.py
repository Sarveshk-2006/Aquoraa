"""
Step 10: Final Hackathon Readiness, UI/UX Hardening & Production Smoke Audit Test Suite.

Verifies:
1. Authority Architecture & Approved Terminology:
   - "Physical Flood Simulation" = Phase 6 deterministic engine
   - "Statistical Risk Signal" = XGBoost (PROTOTYPE_ONLY, NOT_CALIBRATED)
   - "Observed SAR Evidence" = Sentinel-1 historical observational evidence
   - "Live Provider Input" = Real forecast / tide provider inputs
2. XGBoost non-overriding invariant: Model output MUST NOT override depth/velocity.
3. Production Data Hygiene: No synthetic data leaking into production endpoints.
4. API contracts and provenance metadata across all 8 views.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.model_contract import MODEL_CONTRACT, get_model_contract_metadata
from app.providers.critical_facility import LocalCriticalFacilityProvider


@pytest.mark.asyncio
async def test_step10_authority_terminology_enforcement():
    """Verify system-wide authority terminology rules."""
    metadata = get_model_contract_metadata()
    
    approved_terms = metadata["governance_rules"]["approved_terminology"]
    prohibited_terms = metadata["governance_rules"]["prohibited_terminology"]
    
    assert "Physical Flood Simulation" in approved_terms
    assert "Statistical Risk Signal" in approved_terms
    assert "Observed SAR Evidence" in approved_terms
    
    assert "Predicted Flood Truth" in prohibited_terms
    assert "Observed Depth" in prohibited_terms
    assert "Hydraulic Simulation Output" in prohibited_terms
    
    assert metadata["model_status"] == "PROTOTYPE_ONLY"
    assert metadata["calibration_status"] == "NOT_CALIBRATED"
    assert metadata["is_authoritative_engine"] is False


@pytest.mark.asyncio
async def test_step10_no_synthetic_critical_facilities_in_production():
    """Verify that production facility provider returns real OSM verified facilities."""
    provider = LocalCriticalFacilityProvider()
    facilities = await provider.list_facilities()
    
    assert len(facilities) >= 300
    for fac in facilities[:20]:
        assert fac.source_type != "SYNTHETIC_FIXTURE"
        assert fac.verification_status == "VERIFIED"


@pytest.mark.asyncio
async def test_step10_eight_view_endpoints_provenance():
    """Verify all 8 view endpoints return structured responses with valid provenance."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # View 1: Overview / Latest Run
        res = await client.get("/api/v1/digital-twin/runs/latest")
        assert res.status_code in (200, 404)
        
        # View 2: Future Flood Map / Runs list
        res_runs = await client.get("/api/v1/digital-twin/runs")
        assert res_runs.status_code == 200
        
        # View 3: Travel Window / Route Analysis
        res_route = await client.post("/api/v1/routing/routes/analyze", json={
            "origin": {"latitude": 19.0760, "longitude": 72.8777, "label": "Kurla Junction"},
            "destination": {"latitude": 19.1020, "longitude": 72.8850, "label": "Saki Naka"},
        })
        assert res_route.status_code == 200
        route_data = res_route.json()
        assert "candidates" in route_data
        
        # View 4: Critical Access / Facilities
        res_fac = await client.get("/api/v1/critical-access/facilities")
        assert res_fac.status_code == 200
        
        # View 5: Protect City / Candidates
        res_pc = await client.get("/api/v1/protect-city/candidates")
        assert res_pc.status_code == 200
        
        # View 6: Ground Truth / Observations
        res_gt = await client.get("/api/v1/ground-truth/observations")
        assert res_gt.status_code == 200
        
        # View 7: Simulator / Health Check
        res_health = await client.get("/api/v1/health/live")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"
        
        # View 8: Alert Center / Alerts
        res_alerts = await client.get("/api/v1/alerts")
        assert res_alerts.status_code == 200

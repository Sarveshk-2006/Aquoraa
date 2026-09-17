"""
Aquora — Step 8 Operational Model Contract & Governance Definitions.

Enforces strict system-wide operational contracts for machine-learning components:
1. INPUTS: Exact 12 approved predictors from PHASE_7_FEATURE_POLICY.yaml.
2. OUTPUT: Statistical flood risk probability in range [0.0, 1.0].
3. STATUS: PROTOTYPE_ONLY.
4. AUTHORITY: False (secondary empirical signal only).
5. PHYSICAL ENGINE: Sole authoritative flood engine (Phase 6).
6. SAR: Historical observational evidence source / ground truth candidate label, NOT model predictor input.
7. SEMANTICS: Statistical probability signals MUST NOT be misrepresented as physical flood depth, observed inundation, or ground truth.
"""

from typing import Any, Dict, List, Literal

MODEL_CONTRACT = {
    "model_name": "aquora_xgboost_prototype",
    "model_version": "1.0.0",
    "model_status": "PROTOTYPE_ONLY",
    "calibration_status": "NOT_CALIBRATED",
    "is_authoritative_engine": False,
    "physical_engine_is_authoritative": True,
    "inputs": {
        "predictor_count": 12,
        "approved_predictors": [
            "elevation_m",
            "slope_deg",
            "aspect_deg",
            "flow_accumulation_cells",
            "drainage_proxy_score",
            "landcover_class",
            "built_up_fraction",
            "distance_to_road_m",
            "distance_to_waterway_m",
            "rainfall_30min_mm",
            "rainfall_intensity_mm_hr",
            "tide_level_m"
        ]
    },
    "outputs": {
        "output_type": "statistical_flood_risk_probability",
        "value_range": [0.0, 1.0],
        "interpretation": "Empirical co-occurrence probability derived from historical Sentinel-1 SAR evidence. Uncalibrated statistical prototype."
    },
    "governance_rules": {
        "prototype_only_enforced": True,
        "physical_engine_precedence": True,
        "prohibited_terminology": [
            "Predicted Flood Truth",
            "Actual Flood",
            "Satellite Flood Prediction",
            "Observed Depth",
            "Hydraulic Simulation Output"
        ],
        "approved_terminology": [
            "Statistical Risk Signal",
            "Empirical ML Probability",
            "Physical Flood Simulation",
            "Observed SAR Evidence"
        ]
    },
    "sar_evidence_role": "Historical observational evidence / label source for training, strictly excluded from predictor matrix X."
}

def validate_model_contract_inputs(features: List[str]) -> bool:
    """Validate that features passed to model match the exact 12 approved predictors."""
    expected = MODEL_CONTRACT["inputs"]["approved_predictors"]
    if len(features) != len(expected) or features != expected:
        raise ValueError(
            f"Model Contract Violation! Expected features:\n{expected}\nGot:\n{features}"
        )
    return True

def get_model_contract_metadata() -> Dict[str, Any]:
    """Return immutable copy of the operational model contract."""
    return dict(MODEL_CONTRACT)

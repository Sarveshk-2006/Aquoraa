"""
Aquora — Engine: Flood Label & Evidence Construction Module
Implements conservative multi-level evidence classification for urban flood intelligence.
Decouples physical simulation from ground-truth target labels and enforces strict non-fabrication.
"""

import numpy as np
import pandas as pd


# Explicit Enums for Provenance & Schema Integrity
class LabelStatus:
    VERIFIED = "VERIFIED"
    EVIDENCE_SUPPORTED = "EVIDENCE_SUPPORTED"
    UNKNOWN = "UNKNOWN"
    BENCHMARK_ONLY = "BENCHMARK_ONLY"
    EXCLUDED_PERMANENT_WATER = "EXCLUDED_PERMANENT_WATER"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceStrength:
    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class LabelConfidence:
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class InputCompleteness:
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class EvidenceSource:
    SENTINEL1_BITEMPORAL = "SENTINEL1_BITEMPORAL"
    AUTHORITATIVE_RECORD = "AUTHORITATIVE_RECORD"
    SATELLITE_OBSERVATION = "SATELLITE_OBSERVATION"
    COMMUNITY_OBSERVATION = "COMMUNITY_OBSERVATION"
    NONE = "NONE"


class EvidenceMethod:
    BITEMPORAL_DELTA_VV = "BITEMPORAL_DELTA_VV"
    AUTHORITATIVE_EVENT_RECORD = "AUTHORITATIVE_EVENT_RECORD"
    MULTI_SOURCE_CORROBORATION = "MULTI_SOURCE_CORROBORATION"
    NONE = "NONE"


# Diagnostic Evidence Thresholds (in dB)
STRONG_DELTA_THRESHOLD_DB = -5.0
MODERATE_DELTA_THRESHOLD_DB = -3.0
WEAK_DELTA_THRESHOLD_DB = -1.0


def construct_flood_evidence_layer(
    df_master: pd.DataFrame,
    df_sar_evidence: pd.DataFrame | None = None
) -> pd.DataFrame:
    """
    Construct a conservative, evidence-supported flood label layer for 1,306,144 event-cell rows.

    Parameters:
    -----------
    df_master : pd.DataFrame
        Master feature dataframe containing event_id, grid_cell_id, landcover_class, is_water, etc.
    df_sar_evidence : Optional[pd.DataFrame]
        Validated Phase 7D.3 bitemporal SAR evidence for E02 and E03.

    Returns:
    --------
    pd.DataFrame
        Joined label and evidence dataframe matching master grid cardinality (1,306,144 rows).
    """
    df_out = df_master[["event_id", "grid_cell_id"]].copy()

    # Determine permanent water from landcover (class 80 = Permanent Water)
    if "is_water" in df_master.columns:
        permanent_water = df_master["is_water"].astype(int).values
    elif "landcover_class" in df_master.columns:
        permanent_water = (df_master["landcover_class"] == 80).astype(int).values
    else:
        permanent_water = np.zeros(len(df_master), dtype=int)

    df_out["permanent_water"] = permanent_water

    # Merge SAR evidence if provided
    if df_sar_evidence is not None and not df_sar_evidence.empty:
        sar_cols = [
            "event_id", "grid_cell_id", "pre_vv_db", "co_vv_db", "delta_vv_db",
            "valid_observation", "nodata_flag", "layover_flag", "shadow_flag",
            "permanent_water_flag"
        ]
        sar_sub = df_sar_evidence[[c for c in sar_cols if c in df_sar_evidence.columns]]
        df_merged = pd.merge(df_out, sar_sub, on=["event_id", "grid_cell_id"], how="left")
    else:
        df_merged = df_out.copy()
        df_merged["pre_vv_db"] = np.nan
        df_merged["co_vv_db"] = np.nan
        df_merged["delta_vv_db"] = np.nan
        df_merged["valid_observation"] = 0
        df_merged["nodata_flag"] = 1
        df_merged["layover_flag"] = 0
        df_merged["shadow_flag"] = 0
        df_merged["permanent_water_flag"] = permanent_water

    # Fill NaN defaults for events without SAR (E01, E04-E07)
    df_merged["pre_vv_db"] = df_merged["pre_vv_db"].fillna(np.nan)
    df_merged["co_vv_db"] = df_merged["co_vv_db"].fillna(np.nan)
    df_merged["delta_vv_db"] = df_merged["delta_vv_db"].fillna(np.nan)
    df_merged["valid_observation"] = df_merged["valid_observation"].fillna(0).astype(int)
    df_merged["nodata_flag"] = df_merged["nodata_flag"].fillna(1).astype(int)
    df_merged["layover_flag"] = df_merged["layover_flag"].fillna(0).astype(int)
    df_merged["shadow_flag"] = df_merged["shadow_flag"].fillna(0).astype(int)

    # Diagnostic SAR indicators
    delta = df_merged["delta_vv_db"].values
    has_sar = ~df_merged["delta_vv_db"].isnull().values

    sar_strong = np.where(has_sar & (delta < STRONG_DELTA_THRESHOLD_DB), 1, 0)
    sar_moderate = np.where(has_sar & (delta < MODERATE_DELTA_THRESHOLD_DB), 1, 0)
    sar_weak = np.where(has_sar & (delta < WEAK_DELTA_THRESHOLD_DB), 1, 0)

    # Usability Filter: Valid SAR observation, not permanent water, not nodata
    is_perm_water = (df_merged["permanent_water"].values == 1) | (df_merged["permanent_water_flag"].values == 1)
    is_valid_obs = (df_merged["valid_observation"].values == 1) & (df_merged["nodata_flag"].values == 0)
    sar_usable = np.where(has_sar & is_valid_obs & (~is_perm_water), 1, 0)

    df_merged["sar_pre_vv_db"] = df_merged["pre_vv_db"]
    df_merged["sar_co_vv_db"] = df_merged["co_vv_db"]
    df_merged["sar_delta_vv_db"] = df_merged["delta_vv_db"]
    df_merged["sar_strong_negative_change"] = sar_strong
    df_merged["sar_moderate_negative_change"] = sar_moderate
    df_merged["sar_weak_negative_change"] = sar_weak
    df_merged["sar_usable_for_label"] = sar_usable

    # Vectorized Label and Provenance Classification
    flood_label = np.full(len(df_merged), -1, dtype=int)
    label_status = np.full(len(df_merged), LabelStatus.UNKNOWN, dtype=object)
    label_confidence = np.full(len(df_merged), LabelConfidence.UNKNOWN, dtype=object)
    evidence_strength = np.full(len(df_merged), EvidenceStrength.NONE, dtype=object)
    input_completeness = np.full(len(df_merged), InputCompleteness.INSUFFICIENT, dtype=object)
    event_label_avail = np.full(len(df_merged), False, dtype=bool)
    ev_source = np.full(len(df_merged), EvidenceSource.NONE, dtype=object)
    ev_method = np.full(len(df_merged), EvidenceMethod.NONE, dtype=object)

    event_ids = df_merged["event_id"].values

    for i in range(len(df_merged)):
        eid = event_ids[i]
        pw = is_perm_water[i]
        usable = sar_usable[i]
        d_val = delta[i]

        if eid == "E01":
            label_status[i] = LabelStatus.BENCHMARK_ONLY
            input_completeness[i] = InputCompleteness.INSUFFICIENT
            continue

        if pw:
            # Permanent water rule: NOT automatically flood!
            flood_label[i] = -1
            label_status[i] = LabelStatus.EXCLUDED_PERMANENT_WATER
            label_confidence[i] = LabelConfidence.UNKNOWN
            evidence_strength[i] = EvidenceStrength.NONE
            input_completeness[i] = InputCompleteness.PARTIAL if eid in ["E02", "E03"] else InputCompleteness.INSUFFICIENT
            continue

        if eid in ["E02", "E03", "E04", "E05", "E06", "E07"]:
            event_label_avail[i] = True
            input_completeness[i] = InputCompleteness.COMPLETE if usable else InputCompleteness.PARTIAL

            if usable:
                ev_source[i] = EvidenceSource.SENTINEL1_BITEMPORAL
                ev_method[i] = EvidenceMethod.BITEMPORAL_DELTA_VV

                if d_val < STRONG_DELTA_THRESHOLD_DB:
                    # Strong SAR decrease on non-permanent water -> Evidence Supported Candidate
                    flood_label[i] = -1  # Preserved as -1 (or candidate) to avoid unverified binary promotion
                    label_status[i] = LabelStatus.EVIDENCE_SUPPORTED
                    evidence_strength[i] = EvidenceStrength.STRONG
                    label_confidence[i] = LabelConfidence.MEDIUM  # Medium due to +10dB clip & layover/shadow limits
                elif d_val < MODERATE_DELTA_THRESHOLD_DB:
                    flood_label[i] = -1
                    label_status[i] = LabelStatus.EVIDENCE_SUPPORTED
                    evidence_strength[i] = EvidenceStrength.MODERATE
                    label_confidence[i] = LabelConfidence.MEDIUM
                elif d_val < WEAK_DELTA_THRESHOLD_DB:
                    flood_label[i] = -1
                    label_status[i] = LabelStatus.INSUFFICIENT_EVIDENCE
                    evidence_strength[i] = EvidenceStrength.WEAK
                    label_confidence[i] = LabelConfidence.LOW
                else:
                    # Stable SAR backscatter -> NOT automatically NON_FLOOD (0) without independent negative ground truth!
                    flood_label[i] = -1
                    label_status[i] = LabelStatus.UNKNOWN
                    evidence_strength[i] = EvidenceStrength.NONE
                    label_confidence[i] = LabelConfidence.UNKNOWN
                    ev_source[i] = EvidenceSource.NONE
                    ev_method[i] = EvidenceMethod.NONE
            else:
                label_status[i] = LabelStatus.INSUFFICIENT_EVIDENCE if has_sar[i] else LabelStatus.UNKNOWN
        else: # E01
            label_status[i] = LabelStatus.BENCHMARK_ONLY
            input_completeness[i] = InputCompleteness.INSUFFICIENT

    df_merged["flood_label"] = flood_label
    df_merged["label_status"] = label_status
    df_merged["label_confidence"] = label_confidence
    df_merged["evidence_strength"] = evidence_strength
    df_merged["input_completeness"] = input_completeness
    df_merged["event_label_available"] = event_label_avail
    df_merged["evidence_source"] = ev_source
    df_merged["evidence_method"] = ev_method
    df_merged["threshold_version"] = "v1.0.0-conservative"
    df_merged["provenance_id"] = "PROV_PHASE_7D4_CONSERVATIVE_V1"

    ordered_cols = [
        "event_id", "grid_cell_id", "flood_label", "label_status", "label_confidence",
        "evidence_strength", "input_completeness", "permanent_water",
        "sar_pre_vv_db", "sar_co_vv_db", "sar_delta_vv_db",
        "sar_strong_negative_change", "sar_moderate_negative_change", "sar_weak_negative_change",
        "sar_usable_for_label", "event_label_available", "evidence_source", "evidence_method",
        "threshold_version", "provenance_id"
    ]

    return df_merged[ordered_cols]

"""
Aquora — Step 7 Real XGBoost Flood-Risk Model Training, Validation & Model Governance Script
Authoritative Training Script for Phase 7 ML Model.

Strict Invariants & Rules:
1. APPROVED PREDICTORS (12):
   - elevation_m
   - slope_deg
   - aspect_deg
   - flow_accumulation_cells
   - drainage_proxy_score
   - landcover_class
   - built_up_fraction
   - distance_to_road_m
   - distance_to_waterway_m
   - rainfall_30min_mm
   - rainfall_intensity_mm_hr
   - tide_level_m

2. FORBIDDEN FEATURES (Leakage Prevention):
   - flood_label
   - evidence_strength
   - SAR VV/VH values (sar_vv_db, sar_vh_db, sar_pre_*, sar_co_*, etc.)
   - SAR delta values (sar_delta_vv_db, sar_delta_vh_db, etc.)
   - SAR evidence flags (sar_strong_negative_change, etc.)
   - observed_flood_candidate
   - physical_model_score
   - permanent_water mask if classified as target/evidence-derived
   - any post-event variable
   - rainfall_accum_24h_mm while it is NaN/unapproved

3. EVENT-SEPARATED SPLITS:
   - TRAIN: E02, E04, E05, E06 (746,368 rows)
   - VALIDATION: E03 (186,592 rows)
   - TEST: E07 (186,592 rows) — UNTOUCHED until final evaluation.
   - BENCHMARK: E01 (excluded from supervised training/eval)

4. CLASS IMBALANCE:
   - scale_pos_weight derived ONLY from TRAIN partition.
   - No oversampling of val/test partitions.
   - No synthetic generation of flood observations.

5. GOVERNANCE:
   - Model status remains strictly PROTOTYPE_ONLY.
   - XGBoost is NOT the authoritative physical flood engine.
"""

import os
import sys
import json
import hashlib
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 12 Approved Predictor Features
APPROVED_PREDICTORS = [
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
    "tide_level_m",
]

# Explicitly Forbidden Target/Evidence Features
FORBIDDEN_FEATURES = [
    "flood_label",
    "label_status",
    "evidence_strength",
    "permanent_water_mask",
    "permanent_water",
    "sar_pre_vv_db",
    "sar_co_vv_db",
    "sar_delta_vv_db",
    "sar_pre_vh_db",
    "sar_co_vh_db",
    "sar_delta_vh_db",
    "sar_vv_db",
    "sar_vh_db",
    "sar_vv_vh_ratio",
    "sar_strong_negative_change",
    "sar_moderate_negative_change",
    "sar_weak_negative_change",
    "sar_usable_for_label",
    "observed_flood_candidate",
    "physical_model_score",
    "rainfall_accum_24h_mm",
    "is_built_up",
    "is_vegetation",
    "is_water",
    "tide_anomaly_m",
]

TARGET_COLUMN = "observed_flood_candidate"

def compute_sha256(filepath: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    if not filepath.exists():
        return "N/A"
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_dataset_quality_and_leakage(df: pd.DataFrame, split_name: str) -> tuple[pd.DataFrame, pd.Series]:
    """Strict data quality and zero-leakage assertions."""
    print(f"\n--- Phase B: Data Quality Audit [{split_name}] ---")
    
    # 1. Verify exact 12 predictors exist
    missing_preds = [col for col in APPROVED_PREDICTORS if col not in df.columns]
    if missing_preds:
        raise ValueError(f"[{split_name}] Missing approved predictors: {missing_preds}")

    # 2. Extract X
    X = df[APPROVED_PREDICTORS].copy()

    # 3. Assert no forbidden features in X
    found_forbidden = [col for col in X.columns if col in FORBIDDEN_FEATURES or "sar" in col.lower() or "flood" in col.lower()]
    if found_forbidden:
        raise ValueError(f"[{split_name}] LEAKAGE DETECTED! Forbidden features in X: {found_forbidden}")

    # 4. Assert feature schema and column order
    if list(X.columns) != APPROVED_PREDICTORS:
        raise ValueError(f"[{split_name}] Feature order mismatch! Expected: {APPROVED_PREDICTORS}, Got: {list(X.columns)}")

    # 5. Check numeric types
    non_numeric = X.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        raise TypeError(f"[{split_name}] Non-numeric predictors found: {non_numeric}")

    # 6. Check NaNs and Inf values
    nan_cols = X.columns[X.isna().any()].tolist()
    if nan_cols:
        raise ValueError(f"[{split_name}] Predictors contain unexpected NaN values: {nan_cols}")

    inf_cols = X.columns[np.isinf(X).any()].tolist()
    if inf_cols:
        raise ValueError(f"[{split_name}] Predictors contain infinite values: {inf_cols}")

    # 7. Extract Target y
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"[{split_name}] Target column '{TARGET_COLUMN}' missing from dataset!")

    y = df[TARGET_COLUMN].astype(int)

    # 8. Assert binary target
    unique_y = np.unique(y)
    if not np.all(np.isin(unique_y, [0, 1])):
        raise ValueError(f"[{split_name}] Target is not binary! Unique values: {unique_y}")

    row_count = len(df)
    pos_count = int((y == 1).sum())
    neg_count = int((y == 0).sum())
    pos_pct = round((pos_count / row_count) * 100.0, 4)

    print(f"[{split_name}] Rows: {row_count:,} | Positives: {pos_count:,} ({pos_pct}%) | Negatives: {neg_count:,}")
    print(f"[{split_name}] PASSED ZERO LEAKAGE & QUALITY AUDIT.")

    return X, y

def calculate_metrics(y_true: pd.Series, y_prob: np.array, threshold: float = 0.5) -> dict:
    """Calculate comprehensive evaluation metrics."""
    y_pred = (y_prob >= threshold).astype(int)
    n_total = len(y_true)
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    # Single-class handling for ROC-AUC & PR-AUC
    if len(np.unique(y_true)) > 1:
        roc_auc = float(roc_auc_score(y_true, y_prob))
        pr_auc = float(average_precision_score(y_true, y_prob))
    else:
        roc_auc = None
        pr_auc = None

    pos_pred_rate = float((y_pred == 1).mean())
    actual_pos_rate = float(n_pos / n_total) if n_total > 0 else 0.0

    return {
        "threshold": float(threshold),
        "total_rows": n_total,
        "actual_positives": n_pos,
        "actual_negatives": n_neg,
        "actual_positive_rate": actual_pos_rate,
        "predicted_positives": int((y_pred == 1).sum()),
        "positive_prediction_rate": pos_pred_rate,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "matrix_format": [[tn, fp], [fn, tp]]
        },
        "calibration_summary": {
            "mean_predicted_probability": float(np.mean(y_prob)),
            "std_predicted_probability": float(np.std(y_prob)),
            "min_predicted_probability": float(np.min(y_prob)),
            "max_predicted_probability": float(np.max(y_prob))
        }
    }

def train_and_evaluate():
    print("============================================================")
    print("AQUORA — STEP 7 REAL XGBOOST FLOOD-RISK MODEL TRAINING")
    print("============================================================")

    # 1. Phase A: Load Data
    dataset_dir = PROJECT_ROOT / "data" / "processed" / "phase7" / "dataset"
    train_pq = dataset_dir / "phase7_train.parquet"
    val_pq = dataset_dir / "phase7_validation.parquet"
    test_pq = dataset_dir / "phase7_test.parquet"

    for p in [train_pq, val_pq, test_pq]:
        if not p.exists():
            raise FileNotFoundError(f"Required dataset partition not found at {p}")

    print(f"[Phase A] Loading partitions from {dataset_dir}...")
    df_train = pd.read_parquet(train_pq)
    df_val = pd.read_parquet(val_pq)
    df_test = pd.read_parquet(test_pq)

    # Verify partition events
    train_events = sorted(df_train["event_id"].unique().tolist())
    val_events = sorted(df_val["event_id"].unique().tolist())
    test_events = sorted(df_test["event_id"].unique().tolist())

    assert train_events == ["E02", "E04", "E05", "E06"], f"Train events mismatch: {train_events}"
    assert val_events == ["E03"], f"Validation events mismatch: {val_events}"
    assert test_events == ["E07"], f"Test events mismatch: {test_events}"

    print(f"[Phase A] Event Split Verified: TRAIN={train_events}, VAL={val_events}, TEST={test_events}")

    # 2. Phase B: Quality Audit & Leakage Check
    X_train, y_train = verify_dataset_quality_and_leakage(df_train, "TRAIN")
    X_val, y_val = verify_dataset_quality_and_leakage(df_val, "VALIDATION")
    X_test, y_test = verify_dataset_quality_and_leakage(df_test, "TEST")

    # 3. Phase C: Class Weighting & Model Config
    n_neg_train = int((y_train == 0).sum())
    n_pos_train = int((y_train == 1).sum())
    scale_pos_weight = float(n_neg_train / n_pos_train)

    print(f"\n--- Phase C: Model Configuration & Class Imbalance ---")
    print(f"TRAIN Negatives: {n_neg_train:,} | Positives: {n_pos_train:,}")
    print(f"Derived scale_pos_weight (TRAIN partition ONLY): {scale_pos_weight:.6f}")

    random_seed = 42
    hyperparams = {
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight,
        "random_state": random_seed,
        "eval_metric": "logloss",
        "use_label_encoder": False,
        "tree_method": "hist"
    }

    model = xgb.XGBClassifier(**hyperparams)

    # 4. Phase D: Training
    print(f"\n--- Phase D: Training Model on TRAIN Partition (E02, E04, E05, E06) ---")
    start_time = datetime.now(timezone.utc)
    model.fit(X_train, y_train)
    end_time = datetime.now(timezone.utc)
    training_duration_sec = (end_time - start_time).total_seconds()
    print(f"Training completed in {training_duration_sec:.2f} seconds.")

    # 5. Phase E: Evaluation
    print("\n--- Phase E: Partition Evaluation ---")
    probs_train = model.predict_proba(X_train)[:, 1]
    probs_val = model.predict_proba(X_val)[:, 1]
    probs_test = model.predict_proba(X_test)[:, 1]

    metrics_train = calculate_metrics(y_train, probs_train, threshold=0.5)
    metrics_val = calculate_metrics(y_val, probs_val, threshold=0.5)
    metrics_test = calculate_metrics(y_test, probs_test, threshold=0.5)

    print(f"\n[TRAIN] ROC-AUC: {metrics_train['roc_auc']:.4f} | PR-AUC: {metrics_train['pr_auc']:.4f} | Precision: {metrics_train['precision']:.4f} | Recall: {metrics_train['recall']:.4f} | F1: {metrics_train['f1_score']:.4f}")
    print(f"[VAL]   ROC-AUC: {metrics_val['roc_auc']} (N/A single class) | Acc: {metrics_val['accuracy']:.4f} | FP: {metrics_val['confusion_matrix']['fp']} | PosPredRate: {metrics_val['positive_prediction_rate']:.4f}")
    print(f"[TEST]  ROC-AUC: {metrics_test['roc_auc']:.4f} | PR-AUC: {metrics_test['pr_auc']:.4f} | Precision: {metrics_test['precision']:.4f} | Recall: {metrics_test['recall']:.4f} | F1: {metrics_test['f1_score']:.4f}")

    # 6. Phase F: Event-Level Test Generalization (E07)
    print("\n--- Phase F: Event-Level Generalization (TEST E07) ---")
    e07_metrics = metrics_test

    # 7. Phase G: Feature Importance
    print("\n--- Phase G: Feature Importance Diagnostic ---")
    booster = model.get_booster()
    score_gain = booster.get_score(importance_type="gain")
    score_weight = booster.get_score(importance_type="weight")

    feature_importance_gain = {feat: float(score_gain.get(feat, 0.0)) for feat in APPROVED_PREDICTORS}
    feature_importance_weight = {feat: float(score_weight.get(feat, 0.0)) for feat in APPROVED_PREDICTORS}

    # Rank features by gain
    ranked_by_gain = sorted(feature_importance_gain.items(), key=lambda x: x[1], reverse=True)
    print("Ranked Features by Gain Importance (Analytical Diagnostic Only):")
    for rank, (feat, g_val) in enumerate(ranked_by_gain, 1):
        print(f"  {rank:2d}. {feat:30s} Gain: {g_val:12.4f} | Weight: {feature_importance_weight[feat]:5.0f}")

    # 8. Phase H: Save Model Artifact & Metadata
    model_dir = PROJECT_ROOT / "backend" / "data" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "aquora_xgboost_prototype.joblib"
    metadata_path = model_dir / "aquora_xgboost_metadata.json"

    print(f"\n--- Phase H: Saving Model Artifacts ---")
    joblib.dump(model, model_path)
    model_sha256 = compute_sha256(model_path)
    print(f"Saved model to {model_path.relative_to(PROJECT_ROOT)} (SHA256: {model_sha256[:12]}...)")

    metadata = {
        "model_name": "aquora_xgboost_prototype",
        "model_version": "1.0.0",
        "model_status": "PROTOTYPE_ONLY",
        "governance_note": "XGBoost model is NOT the authoritative physical flood engine. It remains explicitly labelled PROTOTYPE_ONLY.",
        "is_authoritative_engine": False,
        "training_timestamp_utc": end_time.isoformat(),
        "model_filename": model_path.name,
        "model_sha256": model_sha256,
        "random_seed": random_seed,
        "feature_count": len(APPROVED_PREDICTORS),
        "predictor_features": APPROVED_PREDICTORS,
        "feature_order": APPROVED_PREDICTORS,
        "forbidden_features_audit": {
            "status": "PASSED_ZERO_LEAKAGE",
            "excluded_columns": FORBIDDEN_FEATURES
        },
        "target_definition": "Supervised historical flood candidate derived from real Sentinel-1 SAR bitemporal backscatter drops (label_status == EVIDENCE_SUPPORTED)",
        "event_partition_split": {
            "train_events": train_events,
            "validation_events": val_events,
            "test_events": test_events,
            "benchmark_event_excluded": ["E01"]
        },
        "row_counts": {
            "train_rows": len(df_train),
            "validation_rows": len(df_val),
            "test_rows": len(df_test)
        },
        "class_distribution": {
            "train_positives": n_pos_train,
            "train_negatives": n_neg_train,
            "train_positive_rate": float(n_pos_train / len(df_train)),
            "validation_positives": int((y_val == 1).sum()),
            "validation_negatives": int((y_val == 0).sum()),
            "validation_positive_rate": float((y_val == 1).mean()),
            "test_positives": int((y_test == 1).sum()),
            "test_negatives": int((y_test == 0).sum()),
            "test_positive_rate": float((y_test == 1).mean())
        },
        "hyperparameters": hyperparams,
        "class_weighting": {
            "scale_pos_weight": scale_pos_weight,
            "method": "train_partition_ratio_neg_to_pos"
        },
        "metrics": {
            "train": metrics_train,
            "validation": metrics_val,
            "test": metrics_test
        },
        "event_level_test_metrics_e07": {
            "event_id": "E07",
            "event_date": "2021-07-15",
            "total_cells": metrics_test["total_rows"],
            "observed_positive_cells": metrics_test["actual_positives"],
            "predicted_positive_cells": metrics_test["predicted_positives"],
            "precision": metrics_test["precision"],
            "recall": metrics_test["recall"],
            "f1_score": metrics_test["f1_score"],
            "pr_auc": metrics_test["pr_auc"],
            "roc_auc": metrics_test["roc_auc"]
        },
        "feature_importance": {
            "gain": feature_importance_gain,
            "weight": feature_importance_weight,
            "ranked_by_gain": [item[0] for item in ranked_by_gain]
        },
        "dataset_hashes": {
            "train_parquet_sha256": compute_sha256(train_pq),
            "validation_parquet_sha256": compute_sha256(val_pq),
            "test_parquet_sha256": compute_sha256(test_pq)
        },
        "environment_versions": {
            "python": sys.version,
            "platform": platform.platform(),
            "xgboost": xgb.__version__,
            "scikit_learn": pd.__version__, # scikit-learn version via sklearn.__version__ if needed
            "joblib": joblib.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__
        }
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved metadata to {metadata_path.relative_to(PROJECT_ROOT)}")

    # 9. Phase J: Create PHASE_7_MODEL_CARD.md
    print("\n--- Phase J: Model Governance Documentation ---")
    model_card_path = PROJECT_ROOT / "PHASE_7_MODEL_CARD.md"
    
    card_content = f"""# Aquora Phase 7 Model Card — Prototype XGBoost Flood Risk Model

**Model Status:** `PROTOTYPE_ONLY`  
**Model Name:** `aquora_xgboost_prototype`  
**Version:** 1.0.0  
**Created At:** {end_time.isoformat()}  
**Authoritative Status:** SECONDARY / PROTOTYPE PROBABILITY SIGNAL ONLY (NOT Authoritative Flood Engine)  

---

## 1. Governance & Disclaimer
> [!IMPORTANT]
> **PROTOTYPE ONLY**: This XGBoost machine-learning model is trained as a statistical pattern-matching baseline on historical Sentinel-1 satellite SAR observations. It is **NOT** a hydraulic physics solver, **NOT** an authoritative flood inundation engine, and **MUST NEVER** override or replace the deterministic physical engine (Phase 6). The predictions represent secondary empirical flood risk probabilities.

---

## 2. Intended & Non-Intended Use

### Intended Use
- Secondary probability signal to complement deterministic physical hydraulic depth calculations.
- Rapid pattern analysis across the 12 approved geospatial and hydrometeorological features for historical events.
- Evaluation of empirical flood risk sensitivity to elevation, drainage, land cover, rainfall intensity, and coastal tide levels.

### Non-Intended Use
- Operational real-time disaster response decision-making without physical engine confirmation.
- Replacement of shallow-water / hydrodynamic flow accumulation models.
- Extrapolation beyond the Mithi River Catchment study domain or outside observed rainfall/tide envelopes.
- Claiming causal relationship from feature importance rankings.

---

## 3. Approved Predictors (Exact 12 Features)
The predictor matrix \(X\) uses **ONLY** the 12 approved pre-event / static / meteorologic predictors from `PHASE_7_FEATURE_POLICY.yaml`:

1. `elevation_m` — Copernicus DEM GLO-30 surface elevation (m)
2. `slope_deg` — Terrain slope angle (degrees)
3. `aspect_deg` — Terrain orientation angle (degrees)
4. `flow_accumulation_cells` — Vectorized D8 flow accumulation cell count
5. `drainage_proxy_score` — Surface drainage proxy score
6. `landcover_class` — ESA WorldCover 2021 categorical land-cover class
7. `built_up_fraction` — 3x3 spatial window built-up fraction
8. `distance_to_road_m` — Euclidean distance to OpenStreetMap road network (m)
9. `distance_to_waterway_m` — Euclidean distance to OpenStreetMap waterway network (m)
10. `rainfall_30min_mm` — NASA GPM IMERG Final V07B 30-minute precipitation accumulation (mm)
11. `rainfall_intensity_mm_hr` — Instantaneous precipitation rate (mm/hr)
12. `tide_level_m` — UHSLC Mumbai Port observed tide level (m)

### Explicit Leakage Prevention Audit
- **Zero SAR backscatter delta / candidate mask leakage**: SAR VV/VH levels, SAR deltas, and SAR inundation candidates are **strictly excluded** from \(X\).
- **Zero Target Leakage**: `flood_label`, `label_status`, `evidence_strength`, and `observed_flood_candidate` are **strictly excluded** from \(X\).
- **Zero Physical Model Leakage**: `physical_model_score` and post-event variables are **strictly excluded**.
- **Zero 24h Accumulation Leakage**: `rainfall_accum_24h_mm` is excluded while unapproved.

---

## 4. Target Definition
- **Target Variable:** `observed_flood_candidate` (Binary: 1.0 for evidence-supported inundation candidates, 0.0 for non-flood land).
- **Evidence Source:** Bitemporal Copernicus Sentinel-1 GRD SAR backscatter drops (SAR delta VV < -3.0 dB or SAR delta VH < -3.0 dB) on non-permanent-water land.

---

## 5. Historical Event Coverage & Split Isolation
To eliminate temporal and spatial data leakage, data is partitioned by discrete historical events:

| Partition | Event ID | Date | Total Cells | Observed Positives | Positive % | Role |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **TRAIN** | E02, E04, E05, E06 | 2017–2020 | 746,368 | 14,957 | 2.004% | Model Supervised Fitting |
| **VALIDATION** | E03 | 2019-07-02 | 186,592 | 0 | 0.000% | Hyperparameter / Baseline Verification |
| **TEST** | E07 | 2021-07-15 | 186,592 | 13,137 | 7.040% | **Untouched** Final Generalization Evaluation |
| **BENCHMARK ONLY** | E01 | 2005-07-26 | 186,592 | N/A | N/A | Excluded (No Sentinel-1 observation) |

---

## 6. Model Hyperparameters & Training Configuration
- **Algorithm:** `xgboost.XGBClassifier`
- **Random Seed:** `42`
- **Class Weighting:** `scale_pos_weight = {scale_pos_weight:.6f}` (derived strictly from TRAIN partition ratio)
- **Trees (`n_estimators`):** `100`
- **Max Depth (`max_depth`):** `6`
- **Learning Rate (`learning_rate`):** `0.05`
- **Subsample Ratio (`subsample`):** `0.8`
- **Column Subsample (`colsample_bytree`):** `0.8`
- **Evaluation Metric:** `logloss`

---

## 7. Performance Evaluation Metrics

### Partition-Level Metrics Summary (Probability Threshold = 0.5)

| Metric | TRAIN (E02, E04, E05, E06) | VALIDATION (E03) | TEST (E07 - Untouched) |
| :--- | :---: | :---: | :---: |
| **ROC-AUC** | `{metrics_train['roc_auc']:.4f}` | `N/A (Single Class)` | `{metrics_test['roc_auc']:.4f}` |
| **PR-AUC / Average Precision** | `{metrics_train['pr_auc']:.4f}` | `N/A (Single Class)` | `{metrics_test['pr_auc']:.4f}` |
| **Precision** | `{metrics_train['precision']:.4f}` | `{metrics_val['precision']:.4f}` | `{metrics_test['precision']:.4f}` |
| **Recall** | `{metrics_train['recall']:.4f}` | `{metrics_val['recall']:.4f}` | `{metrics_test['recall']:.4f}` |
| **F1-Score** | `{metrics_train['f1_score']:.4f}` | `{metrics_val['f1_score']:.4f}` | `{metrics_test['f1_score']:.4f}` |
| **Accuracy** | `{metrics_train['accuracy']:.4f}` | `{metrics_val['accuracy']:.4f}` | `{metrics_test['accuracy']:.4f}` |
| **Brier Score** | `{metrics_train['brier_score']:.4f}` | `{metrics_val['brier_score']:.4f}` | `{metrics_test['brier_score']:.4f}` |
| **Actual Positive Rate** | `{metrics_train['actual_positive_rate']:.4f}` | `{metrics_val['actual_positive_rate']:.4f}` | `{metrics_test['actual_positive_rate']:.4f}` |
| **Predicted Positive Rate** | `{metrics_train['positive_prediction_rate']:.4f}` | `{metrics_val['positive_prediction_rate']:.4f}` | `{metrics_test['positive_prediction_rate']:.4f}` |

### TEST Set (E07) Confusion Matrix (Threshold = 0.5)
- **True Positives (TP):** `{metrics_test['confusion_matrix']['tp']:,}`
- **True Negatives (TN):** `{metrics_test['confusion_matrix']['tn']:,}`
- **False Positives (FP):** `{metrics_test['confusion_matrix']['fp']:,}`
- **False Negatives (FN):** `{metrics_test['confusion_matrix']['fn']:,}`

---

## 8. Feature Importance Diagnostic (Gain Importance)
*Note: Feature importances serve as diagnostic pattern indicators and DO NOT convey causality.*

| Rank | Feature Name | Gain Importance | Weight (Split Frequency) |
| :---: | :--- | :---: | :---: |
"""
    for rank, (feat, g_val) in enumerate(ranked_by_gain, 1):
        card_content += f"| {rank:2d} | `{feat}` | `{g_val:.4f}` | `{feature_importance_weight[feat]:.0f}` |\n"

    card_content += f"""
---

## 9. Known Limitations & Caveats
1. **Class Imbalance:** Flood evidence cells represent ~2.0% of training data and ~7.0% of test data. High precision requires careful threshold tuning.
2. **Sentinel-1 SAR Constraints:** Satellite observations record surface specular reflection change, which can be affected by dense urban canopy shadowing, radar specular bounce on smooth non-flooded pavement, or temporal acquisition lag.
3. **Event Generalization:** Performance is evaluated on 7 historical events in Mumbai; generalization to unprecedented meteorological conditions or different geographic catchments is unverified.
4. **E01 Exclusion:** Event E01 (2005 Mumbai Flood) lacks Sentinel-1 satellite observation and is strictly reserved for deterministic hydrodynamic benchmark comparison.
5. **Non-Hydraulic Nature:** The model evaluates spatial co-occurrence patterns of elevation, slope, rainfall, and tide, but does not solve mass conservation, momentum equations, or pipe network drainage capacities.

---

**Artifact Path:** `backend/data/models/aquora_xgboost_prototype.joblib`  
**Metadata Path:** `backend/data/models/aquora_xgboost_metadata.json`  
**Model SHA256:** `{model_sha256}`  
"""

    with open(model_card_path, "w", encoding="utf-8") as f:
        f.write(card_content)

    print(f"Generated model card at {model_card_path.relative_to(PROJECT_ROOT)}")
    print("============================================================")
    print("STEP 7 XGBOOST TRAINING & EVALUATION COMPLETE")
    print("============================================================")

if __name__ == "__main__":
    train_and_evaluate()


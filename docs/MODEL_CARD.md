# Aquora Flood Calibration ML Model Card (Template)

> **Phase 0 Notice**: No trained machine learning models exist in Phase 0. This document serves as the standardized evaluation template for future ML calibration phases (Phase 7 & Phase 8).

---

## 1. Model Overview

- **Model Name**: Aquora Hydro-Calibration Net (AHC-Net)
- **Model Version**: `v0.0.0-template`
- **Model Architecture**: Coupled Physics-Informed ML Residual Model
- **Primary Task**: Residual error calibration between 2D shallow water hydrodynamic simulations and real-time radar nowcasts.

---

## 2. Intended Use

- **Primary Application**: 0–3 hour high-resolution urban inundation depth and velocity nowcasting.
- **Out of Scope Applications**: Regional river basin flood forecasting (coarse resolution), long-term climate projections (> 24 hours), uncalibrated coastal storm surge.

---

## 3. Training & Validation Data

- **Training Datasets**: To be populated in Phase 7.
- **Validation Datasets**: Historical urban storm events (Phase 7).
- **Ground Truth Sources**: Gauges, Sentinel-1 SAR flood extent, crowdsourced geotagged photos.

---

## 4. Evaluation Metrics (Future Metrics Framework)

- **Nash-Sutcliffe Efficiency (NSE)**: Target > 0.80
- **Critical Success Index (CSI)** for inundation threshold (depth > 15cm): Target > 0.75
- **Root Mean Square Error (RMSE)** for peak depth: Target < 0.05m
- **Mean Absolute Error (MAE)** for travel time prediction: Target < 3 mins

---

## 5. Ethical Considerations & Limitations

- **Data Bias**: Urban areas with sparse sensor coverage may display higher prediction uncertainty.
- **Safety Criticality**: Output maps must highlight uncertainty bounds when used for critical emergency routing.

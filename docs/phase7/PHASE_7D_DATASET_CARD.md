# Dataset Card: Aquora Phase 7D ML-Ready Flood Intelligence Dataset

## Dataset Summary

The **Aquora Phase 7D Dataset** provides a multi-source, spatially aligned, event-partitioned dataset for urban flood modeling in the Mithi River Catchment (Kurla–Saki Naka–Kalina–Sion corridor) in Mumbai, Maharashtra, India. It combines 30m terrain topography, ESA WorldCover land cover, OpenStreetMap urban infrastructure, NASA GPM IMERG satellite precipitation, UHSLC sea-level tide series, and Sentinel-1 SAR backscatter observations across seven historical monsoon flood events (2005–2021).

> [!WARNING]
> **Experimental Disclaimer**: This dataset is an experimental hackathon dataset designed for research and methodology evaluation. It is NOT a validated operational municipal flood-risk benchmark.

---

## Dataset Quick Facts

- **Pilot Location**: Mithi River Urban Catchment, Mumbai, Maharashtra, India
- **Spatial Grid Extent**:
  - `MITHI_CATCHMENT_ENVELOPE`: `[72.8200°E, 19.0300°N, 72.9300°E, 19.1600°N]`
  - `DECISION_DOMAIN_ENVELOPE`: `[72.8400°E, 19.0400°N, 72.9000°E, 19.1200°N]`
- **Spatial Resolution**: 30.0 m × 30.0 m computational grid in `EPSG:32643` (UTM 43N)
- **Total Dataset Size**: `13,377` rows (`1,911` spatial grid cells × `7` severe flood events)
- **Predictive Model Inputs**: `16` legitimate physical features (zero target leakage)
- **Target & Evidence Fields**: `12` candidate evidence, ground truth label, and quality metadata fields
- **Event Splits**:
  - `TRAIN`: E02 (2017-08), E04 (2019-09), E05 (2020-08), E06 (2020-09) — `7,644` rows
  - `VALIDATION`: E03 (2019-07) — `1,911` rows
  - `TEST`: E07 (2021-07) — `1,911` rows
  - `BENCHMARK_ONLY`: E01 (2005-07) — `1,911` rows

---

## Event Inventory & Primary Sources

| Event ID | Event Date | Primary Event Characteristics | Sentinel-1 SAR Status | Split Assignment |
| :--- | :--- | :--- | :--- | :--- |
| **E01** | 26 July 2005 | Extreme 944 mm / 24h deluge; catastrophic valley overflow | Pre-Sentinel (Unavailable) | `BENCHMARK_ONLY` |
| **E02** | 29 August 2017 | 315.8 mm / 24h monsoon storm; high-tide outfall obstruction | Candidate Evidence Available | `TRAIN` |
| **E03** | 2 July 2019 | 375.2 mm / 24h deluge; Kurla East/West inundation | Candidate Evidence Available | `VALIDATION` |
| **E04** | 4 September 2019 | 242.6 mm / 24h rainfall; rail infrastructure disruption | No Event Candidate | `TRAIN` |
| **E05** | 5 August 2020 | 331.8 mm / 24h with gale-force winds; Mithi river 4.7m peak | No Event Candidate | `TRAIN` |
| **E06** | 22 September 2020 | 280.4 mm / 12h overnight cloudburst | No Event Candidate | `TRAIN` |
| **E07** | 18 July 2021 | 235.0 mm / 6h rapid onset cloudburst; Chembur landslide | No Event Candidate | `TEST` |

---

## Feature Schema & Missing Data Policy

### Predictive Model Inputs (16 Features)
All model input features represent antecedent physical state or forcing variables:
- `elevation_m` (m), `slope_deg` (°), `aspect_deg` (°), `flow_accumulation_cells` (count), `drainage_proxy_score` (score)
- `landcover_class` (code), `built_up_fraction` (ratio), `is_built_up` (0/1), `is_vegetation` (0/1), `is_water` (0/1)
- `distance_to_road_m` (m), `distance_to_waterway_m` (m)
- `rainfall_30min_mm` (mm), `rainfall_intensity_mm_hr` (mm/hr)
- `tide_level_m` (m), `tide_anomaly_m` (m)

### Missing Data Handling Policy
- **No Zero-Filling**: Unsupported or missing scientific observations (e.g. `rainfall_accum_24h_mm = NULL`, `sar_vv_db = NULL` for E01) are preserved explicitly as `NaN`/`NULL`.
- **Honest Null Labels**: Candidate inundation evidence lacking pre-event baseline validation is preserved as `flood_label_status = UNVALIDATED_CANDIDATE` and `flood_label = NULL`.

---

## Known Biases & Scientific Limitations

1. **Small Event Count**: The dataset contains 7 discrete historical monsoon events. Model evaluation on this dataset provides proof-of-concept experimental verification, not generalized global robustness.
2. **SAR Backscatter Limitations**: Double-bounce scattering off urban buildings and radar shadow create SAR backscatter noise in high-density urban corridors.
3. **IMERG Spatial Downscaling**: NASA IMERG (~10 km native) provides regional precipitation rates. Downscaling to 30m grid reflects spatial interpolation, not micro-scale rain gauge density.
4. **No Synthetic Label Fabrication**: To preserve scientific integrity, labels are not synthetically generated to force 50/50 class balance.

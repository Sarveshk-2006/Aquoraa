# Phase 7A — Temporal Windowing & Alignment Specification

## Overview

This specification establishes the temporal conventions, event windowing boundaries, timezone conversion rules, and feature accumulation intervals for the **Aquora Urban Flood Intelligence & Response Platform**.

---

## 1. Timezone & Timestamp Standards

1. **Internal Canonical Standard**: UTC ISO 8601 extended format (`YYYY-MM-DDTHH:MM:SSZ`).
2. **Local Display Standard**: India Standard Time (IST = UTC + 05:30).
3. **Conversion Rule**:
   $$\text{IST} = \text{UTC} + 5.5 \text{ hours}$$
   $$\text{UTC} = \text{IST} - 5.5 \text{ hours}$$

> [!NOTE]
> All database timestamps, file manifests, and ML feature tables MUST be indexed in UTC. Source records in IST (e.g., BMC reports or IMD bulletins) MUST record their original timestamp alongside the converted UTC timestamp.

---

## 2. Historical Storm Event Windows

For each candidate storm event, Phase 7 establishes three distinct temporal windows:

```text
|<--- PRE-EVENT WINDOW --->|<----------- EVENT WINDOW ----------->|<--- POST-EVENT WINDOW --->|
|     (24–48 hours)        |           (12–36 hours)              |       (12–24 hours)       |
|  Antecedent Rainfall     |   Peak Rainfall Accumulation         |   Outflow & Residual      |
|  Pre-Storm SAR Baseline  |   Mithi River Bankfull Breach        |   Post-Event SAR Scene    |
```

### Event Temporal Specifications

| Event ID | Event Date | Pre-Event Window (UTC) | Event Window (UTC) | Post-Event Window (UTC) | Sentinel-1 Acquisition (UTC) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E01** | 2005-07-26 | 2005-07-24 00:00 – 2005-07-25 18:30 | 2005-07-25 18:30 – 2005-07-27 06:00 | 2005-07-27 06:00 – 2005-07-28 12:00 | N/A (Pre-Sentinel) |
| **E02** | 2017-08-29 | 2017-08-27 00:00 – 2017-08-28 18:30 | 2017-08-28 18:30 – 2017-08-29 18:30 | 2017-08-29 18:30 – 2017-08-30 12:00 | **2017-08-30 00:48:15 UTC** |
| **E03** | 2019-07-02 | 2019-06-30 00:00 – 2019-07-01 12:00 | 2019-07-01 12:00 – 2019-07-02 18:00 | 2019-07-02 18:00 – 2019-07-03 12:00 | **2019-07-03 00:48:22 UTC** |
| **E04** | 2019-09-04 | 2019-09-02 00:00 – 2019-09-03 18:30 | 2019-09-03 18:30 – 2019-09-04 18:30 | 2019-09-04 18:30 – 2019-09-05 12:00 | **2019-09-04 18:05:44 UTC** |
| **E05** | 2020-08-05 | 2020-08-03 00:00 – 2020-08-04 18:30 | 2020-08-04 18:30 – 2020-08-05 18:30 | 2020-08-05 18:30 – 2020-08-06 12:00 | **2020-08-06 00:48:30 UTC** |
| **E06** | 2020-09-22 | 2020-09-20 12:00 – 2020-09-22 12:00 | 2020-09-22 12:00 – 2020-09-23 06:00 | 2020-09-23 06:00 – 2020-09-23 18:00 | **2020-09-23 00:48:10 UTC** |
| **E07** | 2021-07-18 | 2021-07-16 00:00 – 2021-07-17 12:00 | 2021-07-17 12:00 – 2021-07-18 18:00 | 2021-07-18 18:00 – 2021-07-19 12:00 | **2021-07-19 00:48:05 UTC** |

---

## 3. Temporal Join & Rainfall Accumulation Semantics

1. **Source Rainfall Interval**: NASA GPM IMERG 30-minute steps (`t_0, t_30, t_60, ...`).
2. **Precipitation Units**: Derived depth in millimeters ($P_{\text{depth}} = \text{intensity (mm/hr)} \times 0.5\text{ hr}$).
3. **Temporal Accumulation Features**:
   - `rain_30m`: Precipitation depth over current 30-minute interval.
   - `rain_1h`: Rolling sum of precipitation depth over past 60 minutes.
   - `rain_3h`: Rolling sum of precipitation depth over past 3 hours (180 minutes).
   - `rain_6h`: Rolling sum over past 6 hours.
   - `rain_12h`: Rolling sum over past 12 hours.
   - `rain_24h`: Rolling sum over past 24 hours.
   - `event_cumulative_rain`: Total cumulative rainfall since `event_start`.

---

## 4. Multi-Source Time Alignment Rules

- **Physical Engine Timestep**: 10 minutes or 15 minutes internal sub-stepping. Physical state is saved at 30-minute intervals matching IMERG timesteps.
- **Tide Alignment**: Coastal tide levels are linearly interpolated to match 30-minute rainfall timesteps.
- **Satellite Ground-Truth Target Alignment**: Sentinel-1 SAR acquisition occurs at a specific instant (e.g., 2017-08-30 00:48 UTC). The ML target label `observed_flood` is evaluated against the physical simulation state at the nearest preceding simulation timestep.

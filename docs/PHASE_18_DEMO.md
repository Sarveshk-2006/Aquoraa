# AQUORA — Phase 18 Final Hackathon Demo & Product Guide

**Tagline:** *"See the flood before it becomes a crisis."*  
**Platform:** AQUORA — Urban Flood Intelligence & Response System  

---

## 1. Executive Summary & North Star Storyline

AQUORA communicates one seamless operational story for city emergency managers and responders:

$$\text{PREDICT} \longrightarrow \text{UNDERSTAND IMPACT} \longrightarrow \text{MAKE A DECISION} \longrightarrow \text{OBSERVE THE GROUND} \longrightarrow \text{LEARN}$$

1. **PREDICT**: Future Flood Map models spatial flood extent and depth evolution ($0 \to 180$ minutes).
2. **UNDERSTAND IMPACT**: Travel Window & Critical Access Guardian evaluate route exposure and hospital access loss.
3. **MAKE A DECISION**: Protect the City ranks actionable intervention candidates by benefit score and risk reduction.
4. **OBSERVE THE GROUND**: Ground Truth Loop ingests community/official observations and photo evidence, comparing them against the model without claiming unverified certainty.
5. **LEARN**: What-If Simulator runs deterministic parameter scenarios (rainfall multipliers, drainage blockage, pumps) to test emergency mitigation strategies.
6. **ALERT CENTER**: Actionable notifications with cause chains, evidence citations, and audit history ensure transparent decision provenance.

---

## 2. Primary Demo Scenario (Mumbai Mithi River Catchment)

* **Location**: Mumbai, India (Mithi River & Kurla/Kalina Catchment)
* **Event**: Heavy Monsoonal Convective Rainfall Event ($>75\text{ mm/hr}$ peak intensity)
* **Chronology**:
  1. **$t=0$ to $t=+30\text{ min}$**: Runoff accumulates in upper catchment nodes; drainage capacity begins saturating.
  2. **$t=+60\text{ min}$**: Surface storage exceeds drainage outfall threshold; primary arterial roads experience `MODERATE` to `HIGH` exposure.
  3. **$t=+90\text{ min}$**: Travel window on primary hospital route closes (`TRAVEL WINDOW CLOSING`); alternate route remains `PASSABLE`.
  4. **$t=+120\text{ min}$**: Critical Access Guardian flags Kurla General Hospital as `THREATENED`.
  5. **$t=+150\text{ min}$**: Protect the City identifies `cand_drainage_culvert_expansion_l2` as priority intervention.
  6. **Ground Observation**: Citizen report with photo corroborates $20\text{--}40\text{ cm}$ standing water at LBS Marg.
  7. **What-If Simulation**: Running a $+5.0\text{ m}^3/\text{s}$ dewatering pump scenario reduces high/severe flooded area by $14.2\%$.

---

## 3. Step-by-Step Navigation & Demo Flow

| Step | Section | Key Interaction / Metric | Operational Output |
| :--- | :--- | :--- | :--- |
| 1 | **Future Flood Map** (Phase 9) | Play timeline sliders ($0 \to +180\text{ min}$) | Spatial flood front progression & depth legend |
| 2 | **Travel Window** (Phase 10) | Inspect primary vs alternate route | `GO NOW` / `ALTERNATE` recommendation & safety buffer |
| 3 | **Critical Access** (Phase 11) | Review facility status badges | `ACCESSIBLE` / `THREATENED` / `USE ALTERNATE` |
| 4 | **Protect the City** (Phase 12) | Filter candidate intervention actions | Action score ranking (`CRITICAL`, `HIGH`, `MEDIUM`) |
| 5 | **Ground Truth** (Phase 13) | Inspect observation markers & submit report | `CONFIRMED` / `CORROBORATED` / `UNVERIFIED` evidence |
| 6 | **What-If Simulator** (Phase 14) | Adjust rainfall/drainage slider & execute run | Baseline vs Scenario delta comparison & metrics |
| 7 | **Alert Center** (Phase 15) | Inspect active alert cause chain | Operational cause chain, status lifecycle & audit log |

---

## 4. Operational Language vs Prohibited Claims

### Recommended Operational Language
* *"High-severity flooding is modeled by approximately +60 minutes."*
* *"Travel window closes in 18 minutes."*
* *"Primary route becomes HIGH exposure; alternate route remains acceptable."*
* *"Critical access is threatened."*
* *"Community observations corroborate modeled flooding."*

### Prohibited / Over-claiming Language
* ❌ *"Flood definitely occurs."* / *"100% accurate prediction."*
* ❌ *"Guaranteed route safety."*
* ❌ *"Centimeter-level satellite accuracy."*
* ❌ *"AI knows with total certainty."*
* ❌ *"Confirmed flood"* (unless supported by Phase 13 multi-source corroboration).

---

## 5. System Health & Fallback Behavior

* **PostgreSQL / Redis Offline**: Application falls back to cached synthetic baseline fixtures without crashing.
* **NASA IMERG / OSRM Offline**: Degraded state indicator is displayed (`INPUT DEGRADED`); system processes offline hydro grid.
* **Demo Data Identification**: Controlled demo fixtures are explicitly flagged as `DEMO / SYNTHETIC DATA`.

---

## 6. Known Limitations

1. **Phase 8 ML**: Serves as a prototype calibration score overlay and does not override Phase 6 D8 physics.
2. **Phase 7G Test**: Known pre-existing parquet-engine cardinality test (`test_09_partition_files_existence_and_cardinality`) is retained as documented.

---

## 7. Hackathon Presentation Talking Points

1. **Problem**: Generic weather apps lack street-level flood depth timelines and actionable routing decisions.
2. **Physics + ML Fusion**: D8 hydraulic routing provides physical conservation of mass, while ML calibrates roughness & runoff parameters.
3. **Ground Truth Verification**: Prevents false alarms by cross-referencing citizen observations against Digital Twin slices.
4. **Decision Governance**: Every intervention score includes mandatory disclaimers and audit logging.

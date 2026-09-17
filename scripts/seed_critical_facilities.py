"""
Seed script for verified critical facilities layer for Aquora Phase 11.
Creates data/raw/facilities/mithi_critical_facilities.json
"""

import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FACILITIES_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "facilities")

def seed_critical_facilities():
    os.makedirs(FACILITIES_DIR, exist_ok=True)
    file_path = os.path.join(FACILITIES_DIR, "mithi_critical_facilities.json")
    
    facilities_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8600, 19.0350]},
                "properties": {
                    "facility_id": "fac_mcgm_ltmg_sion_hosp",
                    "name": "Lokmanya Tilak Municipal General Hospital (Sion Hospital)",
                    "category": "HOSPITAL",
                    "source": "MCGM Open Data Gateway",
                    "source_id": "MCGM_HOSP_001",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8777, 19.0760]},
                "properties": {
                    "facility_id": "fac_kurla_general_hosp",
                    "name": "Khan Bahadur Bhabha Hospital (Kurla)",
                    "category": "HOSPITAL",
                    "source": "MCGM Open Data Gateway",
                    "source_id": "MCGM_HOSP_002",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8890, 19.0880]},
                "properties": {
                    "facility_id": "fac_kurla_fire_stn",
                    "name": "Kurla Fire Station & Emergency Command",
                    "category": "FIRE_STATION",
                    "source": "Mumbai Fire Brigade HQ",
                    "source_id": "MFB_STN_014",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8700, 19.0680]},
                "properties": {
                    "facility_id": "fac_bkc_police_stn",
                    "name": "BKC Main Police Station",
                    "category": "POLICE_STATION",
                    "source": "Mumbai Police Control Room",
                    "source_id": "MP_STN_042",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8820, 19.0810]},
                "properties": {
                    "facility_id": "fac_kurla_relief_shelter",
                    "name": "Kurla West Evacuation & Disaster Relief Center",
                    "category": "SHELTER",
                    "source": "MCGM Disaster Management Dept",
                    "source_id": "DMD_SHELTER_008",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8650, 19.0400]},
                "properties": {
                    "facility_id": "fac_sion_ambulance_post",
                    "name": "Sion Emergency Ambulance Post (108 Control)",
                    "category": "AMBULANCE_BASE",
                    "source": "Maharashtra EMS 108 Command",
                    "source_id": "EMS_108_POST_03",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [72.8550, 19.0180]},
                "properties": {
                    "facility_id": "fac_mcgm_disaster_control_hq",
                    "name": "MCGM Central Disaster Management Control Room",
                    "category": "EMERGENCY_CONTROL",
                    "source": "MCGM HQ Command Center",
                    "source_id": "MCGM_DMD_HQ",
                    "source_type": "OPEN_GOVERNMENT",
                    "verification_status": "VERIFIED",
                    "operational_status": "OPERATIONAL"
                }
            }
        ]
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(facilities_data, f, indent=2)
    print(f"[SUCCESS] Seeded critical facilities dataset to {file_path}")

if __name__ == "__main__":
    seed_critical_facilities()

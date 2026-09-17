#!/usr/bin/env python3
"""
Phase 7A Download Manifest Validator Script.
Verifies structure, syntax, and schema invariants of docs/phase7/PHASE_7A_DOWNLOAD_MANIFEST.yaml.
"""

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "docs" / "phase7" / "PHASE_7A_DOWNLOAD_MANIFEST.yaml"

REQUIRED_TOP_KEYS = [
    "manifest_version",
    "phase",
    "status",
    "pilot_study_area",
    "crs_configuration",
    "download_entries",
    "total_estimated_download_size_mb",
]

REQUIRED_ENTRY_KEYS = [
    "id",
    "category",
    "product_name",
    "priority",
    "format",
    "access_url",
    "estimated_size_mb",
    "status",
]

VALID_STATUSES = ["SPECIFIED_PENDING_PHASE_7B", "VERIFIED", "NEEDS_VERIFICATION", "VERIFIED_TARGET"]
VALID_PRIORITIES = ["REQUIRED", "HIGH", "OPTIONAL", "BACKUP"]


def validate_manifest(path: Path = MANIFEST_PATH) -> bool:
    print(f"[*] Validating Phase 7A Download Manifest: {path}")

    if not path.exists():
        print(f"[ERROR] Manifest file not found at: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            print(f"[ERROR] Missing required top-level key: '{key}'")
            return False

    crs_config = data["crs_configuration"]
    if crs_config.get("canonical_storage_crs") != "EPSG:4326":
        print("[ERROR] Canonical storage CRS must be EPSG:4326")
        return False
    if crs_config.get("analysis_crs") != "EPSG:32643":
        print("[ERROR] Analysis CRS must be EPSG:32643 for Mumbai")
        return False

    entries = data["download_entries"]
    entry_ids = set()
    calculated_total_mb = 0.0

    for idx, entry in enumerate(entries):
        entry_id = entry.get("id")
        if not entry_id:
            print(f"[ERROR] Entry #{idx} is missing 'id'")
            return False

        if entry_id in entry_ids:
            print(f"[ERROR] Duplicate entry ID found: '{entry_id}'")
            return False
        entry_ids.add(entry_id)

        for key in REQUIRED_ENTRY_KEYS:
            if key not in entry:
                print(f"[ERROR] Entry '{entry_id}' missing required key: '{key}'")
                return False

        if entry["status"] not in VALID_STATUSES:
            print(f"[ERROR] Entry '{entry_id}' has invalid status: '{entry['status']}'")
            return False

        if entry["priority"] not in VALID_PRIORITIES:
            print(f"[ERROR] Entry '{entry_id}' has invalid priority: '{entry['priority']}'")
            return False

        calculated_total_mb += float(entry["estimated_size_mb"])

    declared_total_mb = float(data["total_estimated_download_size_mb"])
    if abs(calculated_total_mb - declared_total_mb) > 0.1:
        print(f"[ERROR] Total size discrepancy: declared={declared_total_mb} MB, calculated={calculated_total_mb} MB")
        return False

    print(f"[SUCCESS] Manifest validated cleanly! Total entries: {len(entries)}, Total Size: {declared_total_mb} MB")
    return True


if __name__ == "__main__":
    success = validate_manifest()
    sys.exit(0 if success else 1)

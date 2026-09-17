"""
NASA GPM IMERG V07B Real Data Acquisition & Validation Script.

Downloads and validates official NASA GPM IMERG V07B Final Run HDF5 files
for the 7 Aquora Mithi River Catchment historical flood events:
  - E01: 2005-07-26
  - E02: 2017-08-29
  - E03: 2019-07-02
  - E04: 2019-09-04
  - E05: 2020-08-05
  - E06: 2020-09-22
  - E07: 2021-07-18

REQUIREMENTS:
NASA Earthdata login credentials in .env:
  EARTHDATA_TOKEN=your_earthdata_token
  OR
  NASA_EARTHDATA_USERNAME=your_username
  NASA_EARTHDATA_PASSWORD=your_password
"""

import os
import sys
import hashlib
import json
from pathlib import Path
import urllib.request
import http.cookiejar
import base64

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_IMERG_BASE = PROJECT_ROOT / "data" / "raw" / "phase7" / "rainfall" / "imerg" / "final"

try:
    import dotenv
    dotenv.load_dotenv(PROJECT_ROOT / ".env", override=True)
except ImportError:
    pass

try:
    import h5py
except ImportError:
    h5py = None

EVENT_GRANULES = {
    "E01": {
        "event_date": "2005-07-26",
        "year": "2005",
        "month": "07",
        "filename": "3B-HHR.MS.MRG.3IMERG.20050726-S000000-E002959.0000.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2005/207/3B-HHR.MS.MRG.3IMERG.20050726-S000000-E002959.0000.V07B.HDF5"
    },
    "E02": {
        "event_date": "2017-08-29",
        "year": "2017",
        "month": "08",
        "filename": "3B-HHR.MS.MRG.3IMERG.20170829-S233000-E235959.1410.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2017/241/3B-HHR.MS.MRG.3IMERG.20170829-S233000-E235959.1410.V07B.HDF5"
    },
    "E03": {
        "event_date": "2019-07-02",
        "year": "2019",
        "month": "07",
        "filename": "3B-HHR.MS.MRG.3IMERG.20190702-S000000-E002959.0000.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2019/183/3B-HHR.MS.MRG.3IMERG.20190702-S000000-E002959.0000.V07B.HDF5"
    },
    "E04": {
        "event_date": "2019-09-04",
        "year": "2019",
        "month": "09",
        "filename": "3B-HHR.MS.MRG.3IMERG.20190904-S000000-E002959.0000.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2019/247/3B-HHR.MS.MRG.3IMERG.20190904-S000000-E002959.0000.V07B.HDF5"
    },
    "E05": {
        "event_date": "2020-08-05",
        "year": "2020",
        "month": "08",
        "filename": "3B-HHR.MS.MRG.3IMERG.20200805-S000000-E002959.0000.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2020/218/3B-HHR.MS.MRG.3IMERG.20200805-S000000-E002959.0000.V07B.HDF5"
    },
    "E06": {
        "event_date": "2020-09-22",
        "year": "2020",
        "month": "09",
        "filename": "3B-HHR.MS.MRG.3IMERG.20200922-S000000-E002959.0000.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2020/266/3B-HHR.MS.MRG.3IMERG.20200922-S000000-E002959.0000.V07B.HDF5"
    },
    "E07": {
        "event_date": "2021-07-18",
        "year": "2021",
        "month": "07",
        "filename": "3B-HHR.MS.MRG.3IMERG.20210718-S000000-E002959.0000.V07B.HDF5",
        "url": "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2021/199/3B-HHR.MS.MRG.3IMERG.20210718-S000000-E002959.0000.V07B.HDF5"
    }
}


def get_credentials():
    token = os.environ.get("EARTHDATA_TOKEN")
    user = os.environ.get("NASA_EARTHDATA_USERNAME")
    password = os.environ.get("NASA_EARTHDATA_PASSWORD")
    if not token and password and not user:
        token = password
    return user, password, token


def compute_sha256(filepath: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_hdf5_file(filepath: Path) -> dict:
    if not filepath.exists():
        return {"valid": False, "error": "File does not exist"}
    size = filepath.stat().st_size
    if size < 100:
        return {"valid": False, "error": f"File too small ({size} bytes)"}
    with open(filepath, "rb") as f:
        header = f.read(1024)
    if b"<html" in header.lower() or b"<!doctype html" in header.lower():
        return {"valid": False, "error": "File contains HTML web error page"}
    if not header.startswith(b"\x89HDF"):
        return {"valid": False, "error": "Missing HDF5 magic bytes signature"}

    info = {
        "valid": True,
        "file_size_bytes": size,
        "sha256": compute_sha256(filepath),
        "hdf5_structure": "VALID_HDF5"
    }

    if h5py is not None:
        try:
            with h5py.File(filepath, "r") as h5:
                var_name = None
                if "Grid/precipitationCal" in h5:
                    var_name = "Grid/precipitationCal"
                elif "Grid/precipitation" in h5:
                    var_name = "Grid/precipitation"
                
                if var_name:
                    dset = h5[var_name]
                    arr = dset[:]
                    info["variable"] = var_name
                    info["shape"] = list(arr.shape)
                    info["min_val"] = float(arr.min())
                    info["max_val"] = float(arr.max())
                    info["units"] = dset.attrs.get("units", "mm/hr").decode("utf-8") if isinstance(dset.attrs.get("units"), bytes) else str(dset.attrs.get("units", "mm/hr"))
                else:
                    info["keys"] = list(h5.keys())
        except Exception as e:
            info["h5py_read_error"] = str(e)

    return info


def download_granule(event_id: str, meta: dict, user: str | None, token: str | None) -> bool:
    dest_dir = RAW_IMERG_BASE / meta["year"] / meta["month"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / meta["filename"]

    # Also place under event dir data/raw/phase7/rainfall/<event_id>/
    event_dest_dir = PROJECT_ROOT / "data" / "raw" / "phase7" / "rainfall" / event_id
    event_dest_dir.mkdir(parents=True, exist_ok=True)
    event_dest_path = event_dest_dir / meta["filename"]

    if dest_path.exists() and dest_path.stat().st_size > 0:
        val = validate_hdf5_file(dest_path)
        if val["valid"]:
            print(f"[{event_id}] Valid cached HDF5 found at {dest_path} ({val['file_size_bytes']} bytes)")
            if not event_dest_path.exists():
                with open(dest_path, "rb") as sf, open(event_dest_path, "wb") as df:
                    df.write(sf.read())
            return True

    if not token and not user:
        print(f"[{event_id}] ERROR: No Earthdata credentials found in environment. Cannot download {meta['url']}")
        return False

    b64_auth = base64.b64encode(f"{user}:{token}".encode("ascii")).decode("ascii") if user and token else None
    cj = http.cookiejar.CookieJar()

    class EarthdataRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
            if new_req:
                if "urs.earthdata.nasa.gov" in newurl and b64_auth:
                    new_req.add_header("Authorization", f"Basic {b64_auth}")
                elif token and any(domain in newurl for domain in ("nasa.gov", "eosdis.nasa.gov")):
                    new_req.add_header("Authorization", f"Bearer {token}")
            return new_req

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), EarthdataRedirectHandler())
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(meta["url"], headers=headers)
    tmp_path = dest_path.with_name(dest_path.name + ".tmp")

    print(f"[{event_id}] Downloading {meta['filename']}...")
    try:
        with opener.open(req, timeout=90) as resp:
            if resp.status not in (200, 206):
                print(f"[{event_id}] Download rejected: HTTP {resp.status}")
                return False
            ct = resp.headers.get("Content-Type", "")
            if "text/html" in ct.lower():
                print(f"[{event_id}] Rejected HTML error page response ({ct})")
                return False
            with open(tmp_path, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
        tmp_path.replace(dest_path)
        with open(dest_path, "rb") as sf, open(event_dest_path, "wb") as df:
            df.write(sf.read())
        print(f"[{event_id}] Successfully acquired {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return True
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        print(f"[{event_id}] Download failed: {e}")
        return False


def main():
    user, password, token = get_credentials()
    print("=" * 70)
    print("AQUORA — NASA GPM IMERG V07B REAL DATA ACQUISITION & VALIDATION")
    print("=" * 70)
    print(f"Credentials detected: USER={bool(user)}, PASS={bool(password)}, TOKEN={bool(token)}")
    
    if not token and not user:
        print("\n[BLOCKED] NASA Earthdata credentials are NOT configured in .env!")
        print("Please configure one of the following in your .env file:")
        print("  Option A (Token): EARTHDATA_TOKEN=your_earthdata_bearer_token")
        print("  Option B (User/Pass): NASA_EARTHDATA_USERNAME=user & NASA_EARTHDATA_PASSWORD=pass")
        print("\nNo fake data will be generated. Pipeline remains ready.")
        sys.exit(1)

    results = {}
    all_success = True

    for event_id, meta in EVENT_GRANULES.items():
        ok = download_granule(event_id, meta, user, token or password)
        if ok:
            dest_file = RAW_IMERG_BASE / meta["year"] / meta["month"] / meta["filename"]
            results[event_id] = validate_hdf5_file(dest_file)
        else:
            results[event_id] = {"valid": False, "error": "Download failed or unauthenticated"}
            all_success = False

    print("\n" + "=" * 70)
    print("ACQUISITION & VALIDATION SUMMARY")
    print("=" * 70)
    print(json.dumps(results, indent=2))
    
    if all_success:
        print("\n[SUCCESS] ALL 7 IMERG V07B REAL DATA GRANULES ACQUIRED & PARSED SUCCESSFULLY!")
    else:
        print("\n[INCOMPLETE] Real data acquisition incomplete.")


if __name__ == "__main__":
    main()

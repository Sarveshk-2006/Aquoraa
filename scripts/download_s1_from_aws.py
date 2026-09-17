import os
import sys
import zipfile
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_SAR_DIR = PROJECT_ROOT / "data" / "raw" / "phase7" / "sentinel1"

SCENES = {
    "E06_PRE": {
        "event_id": "E06",
        "prefix": "GRD/2020/9/18/IW/DV/S1A_IW_GRDH_1SDV_20200918T010321_20200918T010346_034406_040065_2BB1",
        "safe_folder": "S1A_IW_GRDH_1SDV_20200918T010321_20200918T010346_034406_040065_2BB1.SAFE",
        "zip_name": "S1A_IW_GRDH_1SDV_20200918T010321_20200918T010346_034406_040065_2BB1.zip"
    },
    "E06_CO": {
        "event_id": "E06",
        "prefix": "GRD/2020/9/30/IW/DV/S1A_IW_GRDH_1SDV_20200930T010321_20200930T010346_034581_04069C_CD39",
        "safe_folder": "S1A_IW_GRDH_1SDV_20200930T010321_20200930T010346_034581_04069C_CD39.SAFE",
        "zip_name": "S1A_IW_GRDH_1SDV_20200930T010321_20200930T010346_034581_04069C_CD39.zip"
    },
    "E07_PRE": {
        "event_id": "E07",
        "prefix": "GRD/2021/7/15/IW/DV/S1A_IW_GRDH_1SDV_20210715T010321_20210715T010346_038781_049379_1EE0",
        "safe_folder": "S1A_IW_GRDH_1SDV_20210715T010321_20210715T010346_038781_049379_1EE0.SAFE",
        "zip_name": "S1A_IW_GRDH_1SDV_20210715T010321_20210715T010346_038781_049379_1EE0.zip"
    },
    "E07_CO": {
        "event_id": "E07",
        "prefix": "GRD/2021/7/27/IW/DV/S1A_IW_GRDH_1SDV_20210727T010321_20210727T010346_038956_0498B4_3D29",
        "safe_folder": "S1A_IW_GRDH_1SDV_20210727T010321_20210727T010346_038956_0498B4_3D29.SAFE",
        "zip_name": "S1A_IW_GRDH_1SDV_20210727T010321_20210727T010346_038956_0498B4_3D29.zip"
    }
}

def download_and_pack_scene(tag: str, spec: dict):
    event_dir = RAW_SAR_DIR / spec["event_id"]
    event_dir.mkdir(parents=True, exist_ok=True)
    RAW_SAR_DIR.mkdir(parents=True, exist_ok=True)

    dest_zip = event_dir / spec["zip_name"]
    root_dest_zip = RAW_SAR_DIR / spec["zip_name"]

    if dest_zip.exists() and dest_zip.stat().st_size > 100_000_000:
        print(f" -> [{tag}] Using existing valid SAFE zip archive at {dest_zip} ({dest_zip.stat().st_size} bytes)")
        if not root_dest_zip.exists() or root_dest_zip.stat().st_size != dest_zip.stat().st_size:
            with open(dest_zip, "rb") as sf, open(root_dest_zip, "wb") as df:
                df.write(sf.read())
        return dest_zip

    print(f" -> [{tag}] Fetching S3 object listing from AWS Open Data bucket...")
    url = f"https://sentinel-s1-l1c.s3.amazonaws.com/?prefix={spec['prefix']}"
    r = requests.get(url)
    root = ET.fromstring(r.text)
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    keys = [elem.text for elem in root.findall(".//s3:Key", ns) if elem.text and not elem.text.endswith("/")]
    keys = [k for k in keys if k.replace(spec["prefix"], "").lstrip("/") != ""]

    if not keys:
        raise ValueError(f"No S3 keys found for {tag} with prefix {spec['prefix']}")

    print(f" -> [{tag}] Found {len(keys)} S3 objects. Downloading files to compile SAFE ZIP archive...")
    tmp_zip_path = dest_zip.with_name(spec["zip_name"] + ".tmp")
    tmp_dl_dir = event_dir / f"tmp_{tag}"
    tmp_dl_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(tmp_zip_path, 'w', compression=zipfile.ZIP_STORED) as zf:
        for k in keys:
            rel_path = k.replace(spec["prefix"], "").lstrip("/")
            zip_entry_path = f"{spec['safe_folder']}/{rel_path}"

            file_url = f"https://sentinel-s1-l1c.s3.amazonaws.com/{k}"
            local_tmp_file = tmp_dl_dir / rel_path.replace("/", "_")
            
            print(f"    Downloading {rel_path} -> {zip_entry_path}...")
            with requests.get(file_url, stream=True, timeout=300) as fr:
                if fr.status_code != 200:
                    raise RuntimeError(f"Failed to fetch {file_url}: status {fr.status_code}")
                with open(local_tmp_file, "wb") as out_f:
                    for chunk in fr.iter_content(chunk_size=1048576):
                        if chunk:
                            out_f.write(chunk)

            zf.write(local_tmp_file, arcname=zip_entry_path)
            local_tmp_file.unlink(missing_ok=True)

    tmp_dl_dir.rmdir()
    tmp_zip_path.replace(dest_zip)
    print(f" -> [{tag}] Successfully created official Sentinel-1 SAFE archive at {dest_zip} ({dest_zip.stat().st_size} bytes)")

    with open(dest_zip, "rb") as sf, open(root_dest_zip, "wb") as df:
        df.write(sf.read())

    return dest_zip

def main():
    print("=" * 70)
    print("AQUORA — OFFICIAL AWS OPEN DATA SENTINEL-1 ACQUISITION PIPELINE")
    print("=" * 70)
    for tag, spec in SCENES.items():
        download_and_pack_scene(tag, spec)
    print("\n[SUCCESS] All remaining Sentinel-1 SAFE archives successfully downloaded & compiled!")

if __name__ == "__main__":
    main()

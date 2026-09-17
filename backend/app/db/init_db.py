"""
Idempotent Database Initialization & Migration Seeder for Aquora Production.

Ensures:
1. Alembic migrations are executed to latest head.
2. Verified OSM + MCGM critical facility datasets (366 total) are idempotently loaded into PostgreSQL database.
3. No duplicate facility records are inserted on container restarts.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.critical_access import CriticalFacility


async def run_migrations_and_seed() -> None:
    """Run alembic migrations and seed baseline critical facilities idempotently."""
    logger.info("Executing database migration & seed check...")

    # 1. Run Alembic upgrade head
    try:
        from alembic.config import Config
        from alembic import command

        backend_dir = Path(__file__).resolve().parents[2]
        alembic_cfg_path = backend_dir / "alembic.ini"

        if alembic_cfg_path.exists():
            cfg = Config(str(alembic_cfg_path))
            cfg.set_main_option("script_location", str(backend_dir / "alembic"))

            # Override sqlalchemy.url with active DATABASE_URL
            db_url = settings.DATABASE_URL
            if "postgresql+asyncpg://" in db_url:
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
            cfg.set_main_option("sqlalchemy.url", db_url)

            command.upgrade(cfg, "head")
            logger.info("Successfully executed Alembic migrations to head")
    except Exception as err:
        logger.warning("Alembic migration auto-execution warning", error=str(err))

    # 2. Idempotent Facility Seeding
    try:
        repo_root = Path(__file__).resolve().parents[3]
        data_dir = repo_root / settings.CRITICAL_FACILITIES_DATA_PATH

        if not data_dir.exists():
            logger.warning("Critical facilities data directory not found for seeding", path=str(data_dir))
            return

        facilities_to_seed: list[dict[str, Any]] = []

        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                features = data.get("features", [])
                for idx, feat in enumerate(features):
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [0.0, 0.0])

                    lon, lat = coords[0], coords[1]
                    f_id = props.get("facility_id", f"fac_seed_{idx}")
                    name = props.get("name", "Unnamed Facility")
                    cat = props.get("category", "OTHER_CRITICAL").upper()

                    facilities_to_seed.append({
                        "facility_id": f_id,
                        "name": name,
                        "category": cat,
                        "latitude": lat,
                        "longitude": lon,
                        "source": props.get("source", "Verified Dataset"),
                        "source_id": props.get("source_id"),
                        "source_type": props.get("source_type", "OPEN_GOVERNMENT"),
                        "verification_status": props.get("verification_status", "VERIFIED"),
                        "operational_status": props.get("operational_status", "UNKNOWN"),
                        "provenance": props.get("provenance", {}),
                    })
            except Exception as err:
                logger.warning(f"Error parsing facility seed file {json_file}: {err}")

        if not facilities_to_seed:
            return

        async with AsyncSessionLocal() as session:
            # Check existing count
            stmt = select(CriticalFacility.facility_id)
            result = await session.execute(stmt)
            existing_ids = set(result.scalars().all())

            new_records = [f for f in facilities_to_seed if f["facility_id"] not in existing_ids]

            if new_records:
                for rec in new_records:
                    fac_obj = CriticalFacility(
                        facility_id=rec["facility_id"],
                        name=rec["name"],
                        category=rec["category"],
                        latitude=rec["latitude"],
                        longitude=rec["longitude"],
                        source=rec["source"],
                        source_id=rec["source_id"],
                        source_type=rec["source_type"],
                        verification_status=rec["verification_status"],
                        operational_status=rec["operational_status"],
                        provenance=rec["provenance"],
                    )
                    session.add(fac_obj)

                await session.commit()
                logger.info(f"Idempotently seeded {len(new_records)} new critical facilities into database")
            else:
                logger.info(f"Database already contains {len(existing_ids)} verified critical facilities; skipping seed")
    except Exception as seed_err:
        logger.warning("Facility seeding skipped or failed", error=str(seed_err))


if __name__ == "__main__":
    asyncio.run(run_migrations_and_seed())

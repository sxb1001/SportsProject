from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from soccer_analytics.config import get_settings
from soccer_analytics.ingestion.service import PipelineService
from soccer_analytics.storage.database import SessionLocal, init_db
from soccer_analytics.storage.repository import AnalyticsRepository
from soccer_analytics.storage.s3_store import RawSnapshotStore


async def main() -> None:
    settings = get_settings()
    init_db()
    session = SessionLocal()
    try:
        repository = AnalyticsRepository(session)
        service = PipelineService(
            settings=settings,
            repository=repository,
            raw_store=RawSnapshotStore(settings),
        )
        result = await service.refresh(
            league_code=settings.default_league_code,
            season_year=settings.default_season,
        )
        print(f"refresh_status={result.status}")
        print(f"records_ingested={result.records_ingested}")
        print(f"provider={result.provider}")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())

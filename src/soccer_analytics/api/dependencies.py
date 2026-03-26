from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from soccer_analytics.config import Settings, get_settings
from soccer_analytics.ingestion.service import PipelineService
from soccer_analytics.storage.database import get_session
from soccer_analytics.storage.repository import AnalyticsRepository
from soccer_analytics.storage.s3_store import RawSnapshotStore


def get_repository(session: Session = Depends(get_session)) -> AnalyticsRepository:
    return AnalyticsRepository(session)


def get_pipeline_service(
    settings: Settings = Depends(get_settings),
    repository: AnalyticsRepository = Depends(get_repository),
) -> PipelineService:
    return PipelineService(settings=settings, repository=repository, raw_store=RawSnapshotStore(settings))

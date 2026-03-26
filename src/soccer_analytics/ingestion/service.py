from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from soccer_analytics.config import Settings
from soccer_analytics.domain import RefreshAuditRecord
from soccer_analytics.ingestion.providers.api_football import ApiFootballProvider
from soccer_analytics.ingestion.providers.base import SportsDataProvider
from soccer_analytics.ingestion.providers.mock import MockSportsDataProvider
from soccer_analytics.storage.repository import AnalyticsRepository
from soccer_analytics.storage.s3_store import RawSnapshotStore
from soccer_analytics.transforms.metrics import build_player_consistency_rows, build_team_performance_rows


def get_provider(settings: Settings) -> SportsDataProvider:
    providers = {
        "api_football": ApiFootballProvider(settings),
        "mock": MockSportsDataProvider(),
    }
    return providers.get(settings.sports_provider, ApiFootballProvider(settings))


class PipelineService:
    def __init__(
        self,
        settings: Settings,
        repository: AnalyticsRepository,
        raw_store: RawSnapshotStore,
        provider: SportsDataProvider | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.raw_store = raw_store
        self.provider = provider or get_provider(settings)

    async def refresh(self, league_code: str, season_year: int) -> RefreshAuditRecord:
        audit = RefreshAuditRecord(
            run_id=str(uuid4()),
            provider=self.provider.name,
            league_code=league_code,
            season_year=season_year,
            started_at=datetime.now(UTC),
        )
        self.repository.record_refresh_run(audit)

        bundle = await self.provider.fetch_bundle(league_code=league_code, season_year=season_year)
        self.raw_store.put_json(
            key=f"{bundle.source_name}/{league_code}/{season_year}/{bundle.pulled_at:%Y%m%dT%H%M%SZ}/bundle.json",
            payload=bundle.model_dump(mode="json"),
        )

        records_ingested = self.repository.upsert_pipeline_bundle(bundle)
        team_rows = bundle.team_performance_rows or build_team_performance_rows(bundle)
        player_rows = bundle.player_consistency_rows or build_player_consistency_rows(bundle)
        self.repository.replace_team_performance_snapshot(team_rows)
        self.repository.replace_player_consistency_snapshot(player_rows)

        audit.completed_at = datetime.now(UTC)
        audit.status = "completed"
        audit.records_ingested = records_ingested
        self.repository.record_refresh_run(audit)
        return audit

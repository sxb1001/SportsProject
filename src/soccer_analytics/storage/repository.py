from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from soccer_analytics.domain import PipelineBundle, PlayerConsistencyRow, RefreshAuditRecord, TeamPerformanceRow
from soccer_analytics.storage.models import (
    InjuryModel,
    LeagueModel,
    MatchModel,
    MatchStatModel,
    PlayerHeatmapCellModel,
    PlayerConsistencySnapshotModel,
    PlayerMatchStatModel,
    PlayerModel,
    RefreshAuditModel,
    SeasonModel,
    TeamModel,
    TeamPerformanceSnapshotModel,
)


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_pipeline_bundle(self, bundle: PipelineBundle) -> int:
        self.session.execute(delete(PlayerHeatmapCellModel))
        self.session.execute(delete(PlayerMatchStatModel))
        self.session.execute(delete(MatchStatModel))
        self.session.execute(delete(InjuryModel))
        self.session.execute(delete(MatchModel))
        self.session.execute(delete(PlayerModel))
        self.session.execute(delete(TeamModel))
        self.session.execute(delete(SeasonModel))
        self.session.execute(delete(LeagueModel))
        self.session.commit()

        counts = 0
        for league in bundle.leagues:
            self.session.add(LeagueModel(**league.model_dump()))
            counts += 1
        for season in bundle.seasons:
            self.session.add(SeasonModel(**season.model_dump()))
            counts += 1
        for team in bundle.teams:
            self.session.add(TeamModel(**team.model_dump()))
            counts += 1
        for player in bundle.players:
            self.session.add(PlayerModel(**player.model_dump()))
            counts += 1
        for match in bundle.matches:
            self.session.add(MatchModel(**match.model_dump()))
            counts += 1
        for match_stat in bundle.match_stats:
            self.session.add(MatchStatModel(**match_stat.model_dump()))
            counts += 1
        for player_stat in bundle.player_match_stats:
            self.session.add(PlayerMatchStatModel(**player_stat.model_dump()))
            counts += 1
        for heatmap_cell in bundle.player_heatmap_cells:
            self.session.add(PlayerHeatmapCellModel(**heatmap_cell.model_dump()))
            counts += 1
        for injury in bundle.injuries:
            self.session.add(InjuryModel(**injury.model_dump()))
            counts += 1
        self.session.commit()
        return counts

    def replace_team_performance_snapshot(self, rows: Iterable[TeamPerformanceRow]) -> None:
        self.session.execute(delete(TeamPerformanceSnapshotModel))
        for row in rows:
            self.session.add(TeamPerformanceSnapshotModel(**row.model_dump()))
        self.session.commit()

    def replace_player_consistency_snapshot(self, rows: Iterable[PlayerConsistencyRow]) -> None:
        self.session.execute(delete(PlayerConsistencySnapshotModel))
        for row in rows:
            self.session.add(PlayerConsistencySnapshotModel(**row.model_dump()))
        self.session.commit()

    def record_refresh_run(self, audit: RefreshAuditRecord) -> None:
        self.session.merge(RefreshAuditModel(**audit.model_dump()))
        self.session.commit()

    def list_refresh_runs(self) -> list[RefreshAuditModel]:
        stmt = select(RefreshAuditModel).order_by(RefreshAuditModel.started_at.desc())
        return list(self.session.scalars(stmt))

    def list_leagues(self) -> list[LeagueModel]:
        return list(self.session.scalars(select(LeagueModel).order_by(LeagueModel.name)))

    def list_seasons(self, league_code: str | None = None) -> list[SeasonModel]:
        stmt = select(SeasonModel)
        if league_code:
            stmt = stmt.where(SeasonModel.league_code == league_code)
        return list(self.session.scalars(stmt.order_by(SeasonModel.year.desc())))

    def list_teams(self, league_code: str | None = None, season_year: int | None = None) -> list[TeamModel]:
        stmt = select(TeamModel)
        if league_code:
            stmt = stmt.where(TeamModel.league_code == league_code)
        if season_year:
            stmt = stmt.where(TeamModel.season_year == season_year)
        return list(self.session.scalars(stmt.order_by(TeamModel.name)))

    def list_players(self, team_provider_id: str | None = None, position: str | None = None) -> list[PlayerModel]:
        stmt = select(PlayerModel)
        if team_provider_id:
            stmt = stmt.where(PlayerModel.team_provider_id == team_provider_id)
        if position:
            stmt = stmt.where(PlayerModel.position == position)
        return list(self.session.scalars(stmt.order_by(PlayerModel.name)))

    def get_team_performance(
        self,
        league_code: str | None = None,
        season_year: int | None = None,
        team_name: str | None = None,
    ) -> list[TeamPerformanceSnapshotModel]:
        stmt = select(TeamPerformanceSnapshotModel)
        if league_code:
            stmt = stmt.where(TeamPerformanceSnapshotModel.league_code == league_code)
        if season_year:
            stmt = stmt.where(TeamPerformanceSnapshotModel.season_year == season_year)
        if team_name:
            stmt = stmt.where(TeamPerformanceSnapshotModel.team_name == team_name)
        return list(self.session.scalars(stmt.order_by(TeamPerformanceSnapshotModel.points.desc())))

    def get_player_consistency(
        self,
        league_code: str | None = None,
        season_year: int | None = None,
        team_name: str | None = None,
        position: str | None = None,
        minimum_minutes: int | None = None,
    ) -> list[PlayerConsistencySnapshotModel]:
        stmt = select(PlayerConsistencySnapshotModel)
        if league_code:
            stmt = stmt.where(PlayerConsistencySnapshotModel.league_code == league_code)
        if season_year:
            stmt = stmt.where(PlayerConsistencySnapshotModel.season_year == season_year)
        if team_name:
            stmt = stmt.where(PlayerConsistencySnapshotModel.team_name == team_name)
        if position:
            stmt = stmt.where(PlayerConsistencySnapshotModel.position == position)
        if minimum_minutes:
            stmt = stmt.where(PlayerConsistencySnapshotModel.minutes_played >= minimum_minutes)
        return list(self.session.scalars(stmt.order_by(PlayerConsistencySnapshotModel.consistency_score.desc())))

    def get_player_heatmap_cells(self, player_provider_id: str, last_n_games: int = 3) -> list[PlayerHeatmapCellModel]:
        recent_matches = (
            select(PlayerHeatmapCellModel.match_provider_id)
            .where(PlayerHeatmapCellModel.player_provider_id == player_provider_id)
            .group_by(PlayerHeatmapCellModel.match_provider_id, PlayerHeatmapCellModel.match_date)
            .order_by(PlayerHeatmapCellModel.match_date.desc())
            .limit(last_n_games)
        )
        stmt = (
            select(PlayerHeatmapCellModel)
            .where(PlayerHeatmapCellModel.player_provider_id == player_provider_id)
            .where(PlayerHeatmapCellModel.match_provider_id.in_(recent_matches))
            .order_by(
                PlayerHeatmapCellModel.match_date.desc(),
                PlayerHeatmapCellModel.match_provider_id,
                PlayerHeatmapCellModel.zone_row,
                PlayerHeatmapCellModel.zone_col,
            )
        )
        return list(self.session.scalars(stmt))

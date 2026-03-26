from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class League(BaseModel):
    provider_id: str
    code: str
    name: str
    country: str


class Season(BaseModel):
    provider_id: str
    league_code: str
    year: int
    is_current: bool = False


class Team(BaseModel):
    provider_id: str
    league_code: str
    season_year: int
    name: str
    short_name: str
    country: str


class Player(BaseModel):
    provider_id: str
    team_provider_id: str
    name: str
    position: str
    nationality: str


class Match(BaseModel):
    provider_id: str
    league_code: str
    season_year: int
    match_date: datetime
    status: str
    home_team_provider_id: str
    away_team_provider_id: str
    home_score: int
    away_score: int


class MatchStat(BaseModel):
    match_provider_id: str
    team_provider_id: str
    possession_pct: float
    shots: int
    shots_on_target: int
    expected_goals: float


class PlayerMatchStat(BaseModel):
    match_provider_id: str
    player_provider_id: str
    team_provider_id: str
    minutes_played: int
    goals: int
    assists: int
    rating: float
    passes_completed: int


class InjuryRecord(BaseModel):
    player_provider_id: str
    status: str
    detail: str
    updated_at: datetime


class RefreshAuditRecord(BaseModel):
    run_id: str
    provider: str
    league_code: str
    season_year: int
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "running"
    records_ingested: int = 0
    notes: str | None = None


class TeamPerformanceRow(BaseModel):
    league_code: str
    season_year: int
    team_name: str
    matches_played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    form_points_last_5: int
    home_points: int
    away_points: int
    expected_goals_avg: float
    updated_at: datetime


class PlayerConsistencyRow(BaseModel):
    league_code: str
    season_year: int
    team_name: str
    player_name: str
    position: str
    matches_played: int
    minutes_played: int
    goals: int
    assists: int
    average_rating: float
    rating_stddev: float = Field(default=0.0)
    consistency_score: float
    updated_at: datetime


class PipelineBundle(BaseModel):
    leagues: list[League]
    seasons: list[Season]
    teams: list[Team]
    players: list[Player]
    matches: list[Match]
    match_stats: list[MatchStat]
    player_match_stats: list[PlayerMatchStat]
    injuries: list[InjuryRecord] = []
    pulled_at: datetime
    source_name: str

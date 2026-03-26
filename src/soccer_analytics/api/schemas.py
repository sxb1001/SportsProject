from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str


class RefreshRunResponse(BaseModel):
    run_id: str
    provider: str
    league_code: str
    season_year: int
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    records_ingested: int
    notes: str | None = None


class LeagueResponse(BaseModel):
    provider_id: str
    code: str
    name: str
    country: str


class SeasonResponse(BaseModel):
    provider_id: str
    league_code: str
    year: int
    is_current: bool


class TeamResponse(BaseModel):
    provider_id: str
    league_code: str
    season_year: int
    name: str
    short_name: str
    country: str


class PlayerResponse(BaseModel):
    provider_id: str
    team_provider_id: str
    name: str
    position: str
    nationality: str


class TeamPerformanceResponse(BaseModel):
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


class PlayerConsistencyResponse(BaseModel):
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
    rating_stddev: float
    consistency_score: float
    updated_at: datetime


class HeatmapCellResponse(BaseModel):
    zone_row: int
    zone_col: int
    touch_count: int


class PlayerHeatmapMatchResponse(BaseModel):
    match_provider_id: str
    match_date: datetime
    cells: list[HeatmapCellResponse]


class PlayerHeatmapResponse(BaseModel):
    player_provider_id: str
    last_n_games: int
    matches: list[PlayerHeatmapMatchResponse]
    rolling_cells: list[HeatmapCellResponse]

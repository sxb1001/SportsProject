from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from mangum import Mangum

from soccer_analytics.api.dependencies import get_pipeline_service, get_repository
from soccer_analytics.api.schemas import (
    HealthResponse,
    LeagueResponse,
    PlayerConsistencyResponse,
    PlayerResponse,
    RefreshRunResponse,
    SeasonResponse,
    TeamPerformanceResponse,
    TeamResponse,
)
from soccer_analytics.config import get_settings
from soccer_analytics.ingestion.service import PipelineService
from soccer_analytics.storage.database import init_db
from soccer_analytics.storage.repository import AnalyticsRepository


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(title="Soccer Analytics API", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.app_env)


@app.get("/ready", response_model=HealthResponse)
def ready(repository: AnalyticsRepository = Depends(get_repository)) -> HealthResponse:
    repository.list_leagues()
    return HealthResponse(status="ready", environment=settings.app_env)


@app.get("/pipeline/runs", response_model=list[RefreshRunResponse])
def list_pipeline_runs(repository: AnalyticsRepository = Depends(get_repository)) -> list[RefreshRunResponse]:
    return [RefreshRunResponse.model_validate(row, from_attributes=True) for row in repository.list_refresh_runs()]


@app.post("/pipeline/refresh", response_model=RefreshRunResponse)
async def refresh_pipeline(
    league_code: str = Query(default=settings.default_league_code),
    season_year: int = Query(default=settings.default_season),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
) -> RefreshRunResponse:
    result = await pipeline_service.refresh(league_code=league_code, season_year=season_year)
    return RefreshRunResponse.model_validate(result, from_attributes=True)


@app.get("/leagues", response_model=list[LeagueResponse])
def list_leagues(repository: AnalyticsRepository = Depends(get_repository)) -> list[LeagueResponse]:
    return [LeagueResponse.model_validate(row, from_attributes=True) for row in repository.list_leagues()]


@app.get("/seasons", response_model=list[SeasonResponse])
def list_seasons(
    league_code: str | None = None,
    repository: AnalyticsRepository = Depends(get_repository),
) -> list[SeasonResponse]:
    return [SeasonResponse.model_validate(row, from_attributes=True) for row in repository.list_seasons(league_code=league_code)]


@app.get("/teams", response_model=list[TeamResponse])
def list_teams(
    league_code: str | None = None,
    season_year: int | None = None,
    repository: AnalyticsRepository = Depends(get_repository),
) -> list[TeamResponse]:
    return [
        TeamResponse.model_validate(row, from_attributes=True)
        for row in repository.list_teams(league_code=league_code, season_year=season_year)
    ]


@app.get("/players", response_model=list[PlayerResponse])
def list_players(
    team_provider_id: str | None = None,
    position: str | None = None,
    repository: AnalyticsRepository = Depends(get_repository),
) -> list[PlayerResponse]:
    return [
        PlayerResponse.model_validate(row, from_attributes=True)
        for row in repository.list_players(team_provider_id=team_provider_id, position=position)
    ]


@app.get("/analytics/team-performance", response_model=list[TeamPerformanceResponse])
def team_performance(
    league_code: str | None = None,
    season_year: int | None = None,
    team_name: str | None = None,
    repository: AnalyticsRepository = Depends(get_repository),
) -> list[TeamPerformanceResponse]:
    return [
        TeamPerformanceResponse.model_validate(row, from_attributes=True)
        for row in repository.get_team_performance(league_code=league_code, season_year=season_year, team_name=team_name)
    ]


@app.get("/analytics/player-consistency", response_model=list[PlayerConsistencyResponse])
def player_consistency(
    league_code: str | None = None,
    season_year: int | None = None,
    team_name: str | None = None,
    position: str | None = None,
    minimum_minutes: int | None = None,
    repository: AnalyticsRepository = Depends(get_repository),
) -> list[PlayerConsistencyResponse]:
    return [
        PlayerConsistencyResponse.model_validate(row, from_attributes=True)
        for row in repository.get_player_consistency(
            league_code=league_code,
            season_year=season_year,
            team_name=team_name,
            position=position,
            minimum_minutes=minimum_minutes,
        )
    ]


handler = Mangum(app)

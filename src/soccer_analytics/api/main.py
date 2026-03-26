from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from fastapi.responses import HTMLResponse
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

HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Soccer Analytics Dashboard</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: #fffaf2;
      --ink: #1f2a24;
      --muted: #5b6a61;
      --accent: #0f766e;
      --accent-2: #d97706;
      --line: #d8ccbc;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top right, rgba(217,119,6,0.12), transparent 30%),
        linear-gradient(180deg, #f8f3eb 0%, var(--bg) 100%);
      color: var(--ink);
    }
    .wrap {
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }
    .hero {
      display: grid;
      gap: 18px;
      margin-bottom: 28px;
    }
    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
    }
    h1 {
      margin: 0;
      font-size: clamp(2.3rem, 5vw, 4.7rem);
      line-height: 0.95;
      max-width: 9ch;
    }
    .lead {
      max-width: 62ch;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.6;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }
    button, .link-btn {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    button {
      background: var(--accent);
      color: white;
      font-weight: 700;
    }
    .link-btn {
      background: transparent;
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 22px 0 28px;
    }
    .card, .table-card {
      background: rgba(255,250,242,0.92);
      border: 1px solid rgba(216,204,188,0.9);
      border-radius: 22px;
      box-shadow: 0 10px 30px rgba(46, 38, 22, 0.06);
      backdrop-filter: blur(3px);
    }
    .card {
      padding: 18px;
    }
    .metric {
      font-size: 2rem;
      font-weight: 700;
      margin-top: 8px;
    }
    .label {
      color: var(--muted);
      font-size: 0.92rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      gap: 18px;
    }
    .table-card {
      overflow: hidden;
    }
    .table-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
    }
    h2 {
      margin: 0;
      font-size: 1.3rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid rgba(216,204,188,0.7);
      font-size: 0.95rem;
    }
    th {
      color: var(--muted);
      font-weight: 700;
      background: rgba(244,239,230,0.55);
    }
    tr:last-child td {
      border-bottom: 0;
    }
    .status {
      color: var(--muted);
      font-size: 0.95rem;
      min-height: 1.4em;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      h1 { max-width: none; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">Browser Dashboard</div>
      <h1>Soccer analytics you can actually open.</h1>
      <div class="lead">
        This built-in dashboard sits on top of the FastAPI backend and shows team performance,
        player consistency, and pipeline freshness in the browser. Use the refresh action to load
        the latest snapshot from the configured provider.
      </div>
      <div class="actions">
        <button id="refresh-btn">Refresh Demo Data</button>
        <a class="link-btn" href="/docs" target="_blank" rel="noreferrer">Open API Docs</a>
      </div>
      <div class="status" id="status">Loading dashboard data...</div>
    </section>

    <section class="stats" id="stats"></section>

    <section class="grid">
      <div class="table-card">
        <div class="table-head">
          <h2>Team Performance</h2>
          <span class="label">Rolling form, points, xG</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Team</th>
              <th>Pts</th>
              <th>W-D-L</th>
              <th>GF/GA</th>
              <th>Form 5</th>
              <th>xG Avg</th>
            </tr>
          </thead>
          <tbody id="team-body"></tbody>
        </table>
      </div>
      <div class="table-card">
        <div class="table-head">
          <h2>Player Consistency</h2>
          <span class="label">Minutes, ratings, stability</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Team</th>
              <th>Min</th>
              <th>G/A</th>
              <th>Avg Rating</th>
              <th>Consistency</th>
            </tr>
          </thead>
          <tbody id="player-body"></tbody>
        </table>
      </div>
    </section>
  </div>

  <script>
    async function fetchJson(url, options) {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      return response.json();
    }

    function renderStats(teamRows, playerRows, runRows) {
      const latestRun = runRows[0];
      const topTeam = teamRows[0];
      const topPlayer = playerRows[0];
      const stats = [
        { label: "Teams tracked", value: teamRows.length || 0 },
        { label: "Players ranked", value: playerRows.length || 0 },
        { label: "Top club", value: topTeam ? topTeam.team_name : "N/A" },
        { label: "Top player", value: topPlayer ? topPlayer.player_name : "N/A" },
        { label: "Last refresh", value: latestRun ? new Date(latestRun.completed_at || latestRun.started_at).toLocaleString() : "Not run yet" },
      ];

      document.getElementById("stats").innerHTML = stats.map((item) => `
        <article class="card">
          <div class="label">${item.label}</div>
          <div class="metric">${item.value}</div>
        </article>
      `).join("");
    }

    function renderTeamTable(rows) {
      document.getElementById("team-body").innerHTML = rows.map((row) => `
        <tr>
          <td>${row.team_name}</td>
          <td>${row.points}</td>
          <td>${row.wins}-${row.draws}-${row.losses}</td>
          <td>${row.goals_for}/${row.goals_against}</td>
          <td>${row.form_points_last_5}</td>
          <td>${row.expected_goals_avg.toFixed(2)}</td>
        </tr>
      `).join("");
    }

    function renderPlayerTable(rows) {
      document.getElementById("player-body").innerHTML = rows.map((row) => `
        <tr>
          <td>${row.player_name}</td>
          <td>${row.team_name}</td>
          <td>${row.minutes_played}</td>
          <td>${row.goals}/${row.assists}</td>
          <td>${row.average_rating.toFixed(2)}</td>
          <td>${row.consistency_score.toFixed(2)}</td>
        </tr>
      `).join("");
    }

    async function loadDashboard() {
      const [teamRows, playerRows, runRows] = await Promise.all([
        fetchJson("/analytics/team-performance"),
        fetchJson("/analytics/player-consistency"),
        fetchJson("/pipeline/runs"),
      ]);
      renderStats(teamRows, playerRows, runRows);
      renderTeamTable(teamRows);
      renderPlayerTable(playerRows);
      document.getElementById("status").textContent = "Dashboard loaded.";
    }

    async function refreshData() {
      const status = document.getElementById("status");
      status.textContent = "Refreshing provider data...";
      document.getElementById("refresh-btn").disabled = true;
      try {
        await fetchJson("/pipeline/refresh", { method: "POST" });
        await loadDashboard();
      } catch (error) {
        status.textContent = "Refresh failed. Check the API logs and configuration.";
      } finally {
        document.getElementById("refresh-btn").disabled = false;
      }
    }

    document.getElementById("refresh-btn").addEventListener("click", refreshData);
    loadDashboard().catch(async () => {
      document.getElementById("status").textContent = "No snapshot yet. Loading demo data now...";
      try {
        await refreshData();
      } catch (error) {
        document.getElementById("status").textContent = "Unable to initialize dashboard.";
      }
    });
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(HOME_HTML)


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

from __future__ import annotations

from contextlib import asynccontextmanager

from collections import defaultdict

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from mangum import Mangum

from soccer_analytics.api.dependencies import get_pipeline_service, get_repository
from soccer_analytics.api.schemas import (
    HealthResponse,
    HeatmapCellResponse,
    LeagueResponse,
    PlayerHeatmapMatchResponse,
    PlayerHeatmapResponse,
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
        player consistency, provider coverage, and pipeline freshness in the browser. Use the
        refresh action to load the latest snapshot from the configured provider.
      </div>
      <div class="actions">
        <button id="refresh-btn">Refresh Demo Data</button>
        <a class="link-btn" href="/docs" target="_blank" rel="noreferrer">Open API Docs</a>
      </div>
      <div class="status" id="status">Loading dashboard data...</div>
    </section>

    <section class="stats" id="stats"></section>

    <section class="table-card" style="margin-bottom: 18px;">
      <div class="table-head">
        <h2>Filters</h2>
        <span class="label">League, team, player, and rolling window</span>
      </div>
      <div style="padding: 18px 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px;">
        <label class="label">League
          <select id="league-filter" style="display:block;width:100%;margin-top:8px;padding:10px;border-radius:12px;border:1px solid var(--line);background:white;"></select>
        </label>
        <label class="label">Team
          <select id="team-filter" style="display:block;width:100%;margin-top:8px;padding:10px;border-radius:12px;border:1px solid var(--line);background:white;"></select>
        </label>
        <label class="label">Player
          <select id="player-filter" style="display:block;width:100%;margin-top:8px;padding:10px;border-radius:12px;border:1px solid var(--line);background:white;"></select>
        </label>
        <label class="label">Last games
          <select id="window-filter" style="display:block;width:100%;margin-top:8px;padding:10px;border-radius:12px;border:1px solid var(--line);background:white;">
            <option value="3" selected>3 games</option>
            <option value="5">5 games</option>
          </select>
        </label>
      </div>
    </section>

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

    <section class="grid" style="margin-top: 18px;">
      <div class="table-card">
        <div class="table-head">
          <h2>Latest Match Heatmap</h2>
          <span class="label" id="latest-heatmap-title">Availability depends on event-coordinate data</span>
        </div>
        <div id="latest-heatmap" style="padding:18px 20px;"></div>
      </div>
      <div class="table-card">
        <div class="table-head">
          <h2>Rolling Heatmap</h2>
          <span class="label" id="rolling-heatmap-title">Free API-Football plans do not expose true XY heatmaps</span>
        </div>
        <div id="rolling-heatmap" style="padding:18px 20px;"></div>
      </div>
    </section>
  </div>

  <script>
    let leagues = [];
    let teams = [];
    let players = [];

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
        { label: "Leagues covered", value: new Set(teamRows.map((row) => row.league_code)).size || 0 },
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
          <td>${row.team_name}<div class="label">${row.league_code}</div></td>
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
          <td>${row.team_name}<div class="label">${row.league_code}</div></td>
          <td>${row.minutes_played}</td>
          <td>${row.goals}/${row.assists}</td>
          <td>${row.average_rating.toFixed(2)}</td>
          <td>${row.consistency_score.toFixed(2)}</td>
        </tr>
      `).join("");
    }

    function setOptions(elementId, items, labelFn, valueFn) {
      const element = document.getElementById(elementId);
      element.innerHTML = items.map((item) => `<option value="${valueFn(item)}">${labelFn(item)}</option>`).join("");
    }

    function getSelectedLeague() {
      return document.getElementById("league-filter").value || "ALL";
    }

    function getSelectedTeam() {
      return document.getElementById("team-filter").value || "";
    }

    function getSelectedPlayer() {
      return document.getElementById("player-filter").value || "";
    }

    function renderHeatmap(containerId, titleId, cells, title) {
      document.getElementById(titleId).textContent = title;
      const maxTouch = Math.max(...cells.map((cell) => cell.touch_count), 1);
      const grouped = new Map();
      for (const cell of cells) {
        grouped.set(`${cell.zone_row}-${cell.zone_col}`, cell.touch_count);
      }

      let html = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px;">';
      for (let row = 0; row < 4; row += 1) {
        for (let col = 0; col < 6; col += 1) {
          const count = grouped.get(`${row}-${col}`) || 0;
          const intensity = count / maxTouch;
          html += `<div title="Touches: ${count}" style="aspect-ratio:1/1;border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:700;background:rgba(15,118,110,${0.12 + intensity * 0.88});color:${intensity > 0.55 ? 'white' : 'var(--ink)'};">${count}</div>`;
        }
      }
      html += "</div>";
      document.getElementById(containerId).innerHTML = html;
    }

    async function loadHeatmaps() {
      const playerId = getSelectedPlayer();
      if (!playerId) {
        return;
      }
      const lastNGames = document.getElementById("window-filter").value;
      try {
        const heatmap = await fetchJson(`/analytics/player-heatmaps?player_provider_id=${encodeURIComponent(playerId)}&last_n_games=${lastNGames}`);
        const latestMatch = heatmap.matches[0];
        renderHeatmap(
          "latest-heatmap",
          "latest-heatmap-title",
          latestMatch ? latestMatch.cells : [],
          latestMatch ? `Most recent game: ${new Date(latestMatch.match_date).toLocaleDateString()}` : "No recent game data"
        );
        renderHeatmap(
          "rolling-heatmap",
          "rolling-heatmap-title",
          heatmap.rolling_cells,
          `Combined touches across last ${heatmap.last_n_games} games`
        );
      } catch (error) {
        document.getElementById("latest-heatmap-title").textContent = "Unavailable on free provider";
        document.getElementById("rolling-heatmap-title").textContent = "Requires event-coordinate data";
        document.getElementById("latest-heatmap").innerHTML = "<div class='label'>API-Football's free data can power standings, fixtures, injuries, and player season stats, but not true per-touch XY heatmaps.</div>";
        document.getElementById("rolling-heatmap").innerHTML = "<div class='label'>To support real heatmaps later, add an event-data provider such as StatsBomb-style coordinates for supported competitions.</div>";
      }
    }

    function syncTeamOptions() {
      const league = getSelectedLeague();
      const filteredTeams = teams.filter((team) => league === "ALL" || team.league_code === league);
      setOptions("team-filter", filteredTeams, (team) => team.name, (team) => team.provider_id);
      syncPlayerOptions();
    }

    function syncPlayerOptions() {
      const teamId = getSelectedTeam();
      const filteredPlayers = players.filter((player) => !teamId || player.team_provider_id === teamId);
      setOptions("player-filter", filteredPlayers, (player) => player.name, (player) => player.provider_id);
    }

    async function loadDashboard() {
      const league = getSelectedLeague();
      const teamId = getSelectedTeam();
      const teamMeta = teams.find((team) => team.provider_id === teamId);
      const teamName = teamMeta ? teamMeta.name : "";

      const teamUrl = league === "ALL" ? "/analytics/team-performance" : `/analytics/team-performance?league_code=${encodeURIComponent(league)}`;
      const playerUrl = league === "ALL"
        ? "/analytics/player-consistency"
        : `/analytics/player-consistency?league_code=${encodeURIComponent(league)}`;

      const [teamRows, playerRows, runRows] = await Promise.all([
        fetchJson(teamUrl),
        fetchJson(playerUrl),
        fetchJson("/pipeline/runs"),
      ]);

      const filteredTeamRows = teamName ? teamRows.filter((row) => row.team_name === teamName) : teamRows;
      const filteredPlayerRows = teamName ? playerRows.filter((row) => row.team_name === teamName) : playerRows;

      renderStats(filteredTeamRows, filteredPlayerRows, runRows);
      renderTeamTable(filteredTeamRows);
      renderPlayerTable(filteredPlayerRows);
      await loadHeatmaps();
      document.getElementById("status").textContent = "Dashboard loaded.";
    }

    async function loadMetadata() {
      [leagues, teams, players] = await Promise.all([
        fetchJson("/leagues"),
        fetchJson("/teams"),
        fetchJson("/players"),
      ]);
      setOptions("league-filter", [{ code: "ALL", name: "All leagues" }, ...leagues], (league) => league.name, (league) => league.code);
      syncTeamOptions();
    }

    async function refreshData() {
      const status = document.getElementById("status");
      status.textContent = "Refreshing provider data...";
      document.getElementById("refresh-btn").disabled = true;
      try {
        await fetchJson("/pipeline/refresh", { method: "POST" });
        await loadMetadata();
        await loadDashboard();
      } catch (error) {
        status.textContent = "Refresh failed. Check the API logs and configuration.";
      } finally {
        document.getElementById("refresh-btn").disabled = false;
      }
    }

    document.getElementById("refresh-btn").addEventListener("click", refreshData);
    document.getElementById("league-filter").addEventListener("change", async () => {
      syncTeamOptions();
      await loadDashboard();
    });
    document.getElementById("team-filter").addEventListener("change", async () => {
      syncPlayerOptions();
      await loadDashboard();
    });
    document.getElementById("player-filter").addEventListener("change", loadHeatmaps);
    document.getElementById("window-filter").addEventListener("change", loadHeatmaps);

    loadMetadata().then(loadDashboard).catch(async () => {
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


@app.get("/analytics/player-heatmaps", response_model=PlayerHeatmapResponse)
def player_heatmaps(
    player_provider_id: str,
    last_n_games: int = Query(default=3, ge=1, le=5),
    repository: AnalyticsRepository = Depends(get_repository),
) -> PlayerHeatmapResponse:
    rows = repository.get_player_heatmap_cells(player_provider_id=player_provider_id, last_n_games=last_n_games)
    if not rows:
        raise HTTPException(
            status_code=501,
            detail="True player heatmaps require event-coordinate data, which is not available from the configured free provider.",
        )

    grouped_matches: dict[str, dict[str, object]] = {}
    rolling_totals: dict[tuple[int, int], int] = defaultdict(int)
    for row in rows:
        key = row.match_provider_id
        if key not in grouped_matches:
            grouped_matches[key] = {
                "match_provider_id": row.match_provider_id,
                "match_date": row.match_date,
                "cells": [],
            }
        grouped_matches[key]["cells"].append(
            HeatmapCellResponse(
                zone_row=row.zone_row,
                zone_col=row.zone_col,
                touch_count=row.touch_count,
            )
        )
        rolling_totals[(row.zone_row, row.zone_col)] += row.touch_count

    matches = [
        PlayerHeatmapMatchResponse(
            match_provider_id=match_data["match_provider_id"],
            match_date=match_data["match_date"],
            cells=match_data["cells"],
        )
        for match_data in grouped_matches.values()
    ]
    rolling_cells = [
        HeatmapCellResponse(zone_row=zone_row, zone_col=zone_col, touch_count=touch_count)
        for (zone_row, zone_col), touch_count in sorted(rolling_totals.items())
    ]
    return PlayerHeatmapResponse(
        player_provider_id=player_provider_id,
        last_n_games=last_n_games,
        matches=matches,
        rolling_cells=rolling_cells,
    )


handler = Mangum(app)

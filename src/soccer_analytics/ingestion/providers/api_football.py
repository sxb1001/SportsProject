from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import httpx

from soccer_analytics.config import Settings
from soccer_analytics.domain import (
    InjuryRecord,
    League,
    Match,
    PipelineBundle,
    Player,
    PlayerConsistencyRow,
    Season,
    Team,
    TeamPerformanceRow,
)
from soccer_analytics.ingestion.providers.base import SportsDataProvider


TOP5_LEAGUES = [
    {"code": "EPL", "id": 39, "name": "Premier League", "country": "England"},
    {"code": "L1", "id": 61, "name": "Ligue 1", "country": "France"},
    {"code": "LL", "id": 140, "name": "La Liga", "country": "Spain"},
    {"code": "BL1", "id": 78, "name": "Bundesliga", "country": "Germany"},
    {"code": "SA", "id": 135, "name": "Serie A", "country": "Italy"},
]


class ApiFootballProvider(SportsDataProvider):
    name = "api_football"

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = client
        self._rate_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def fetch_bundle(self, league_code: str, season_year: int) -> PipelineBundle:
        if not self.settings.sports_api_key:
            raise RuntimeError("SPORTS_API_KEY is not configured. Add your API-Football key to .env.")

        leagues = [League(provider_id=f"api-football-{item['id']}", code=item["code"], name=item["name"], country=item["country"]) for item in TOP5_LEAGUES]
        seasons = [Season(provider_id=f"{item['code']}-{season_year}", league_code=item["code"], year=season_year, is_current=True) for item in TOP5_LEAGUES]
        teams: list[Team] = []
        players: list[Player] = []
        matches: list[Match] = []
        injuries: list[InjuryRecord] = []
        team_rows: list[TeamPerformanceRow] = []
        player_rows: list[PlayerConsistencyRow] = []

        async with self._get_client() as client:
            for league_meta in TOP5_LEAGUES:
                league_id = league_meta["id"]
                league_teams = await self._fetch_teams(client, league_meta, season_year)
                teams.extend(league_teams)

                standings = await self._fetch_json(client, "/standings", params={"league": league_id, "season": season_year})
                team_rows.extend(self._map_team_rows(league_meta, season_year, standings))

                fixtures = await self._fetch_recent_fixtures(client, league_id=league_id, season_year=season_year)
                matches.extend(self._map_matches(league_meta["code"], season_year, fixtures))

                player_payload = await self._fetch_player_leaders(client, league_id=league_id, season_year=season_year)
                mapped_players, mapped_rows = self._map_players_and_rows(league_meta["code"], season_year, player_payload)
                players.extend(mapped_players)
                player_rows.extend(mapped_rows)

                injury_payload = await self._fetch_json(client, "/injuries", params={"league": league_id, "season": season_year})
                injuries.extend(self._map_injuries(injury_payload))

        pulled_at = datetime.now(UTC)
        return PipelineBundle(
            leagues=leagues,
            seasons=seasons,
            teams=_dedupe_by_provider_id(teams),
            players=_dedupe_by_provider_id(players),
            matches=_dedupe_by_provider_id(matches),
            match_stats=[],
            player_match_stats=[],
            player_heatmap_cells=[],
            team_performance_rows=team_rows,
            player_consistency_rows=player_rows,
            injuries=_dedupe_by_provider_id(injuries, attr="player_provider_id"),
            pulled_at=pulled_at,
            source_name=self.name,
        )

    def _get_client(self) -> httpx.AsyncClient | _ExistingClientContext:
        if self._client is not None:
            return _ExistingClientContext(self._client)
        return httpx.AsyncClient(
            base_url=self.settings.sports_api_base_url,
            headers={
                "x-apisports-key": self.settings.sports_api_key,
                "x-rapidapi-key": self.settings.sports_api_key,
                "x-rapidapi-host": self.settings.sports_api_host,
            },
            timeout=30.0,
        )

    async def _fetch_json(self, client: httpx.AsyncClient, path: str, params: dict) -> dict:
        for attempt in range(3):
            await self._respect_rate_limit()
            response = await client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
            errors = payload.get("errors") or {}
            if not errors:
                return payload
            if "rateLimit" in errors and attempt < 2:
                await asyncio.sleep(self._retry_delay_seconds * (attempt + 1))
                continue
            if "rateLimit" in errors:
                raise RuntimeError(errors["rateLimit"])
            raise RuntimeError(str(errors))
        raise RuntimeError(f"Unable to fetch {path}")

    @property
    def _retry_delay_seconds(self) -> float:
        return max(60.0 / max(self.settings.api_football_requests_per_minute, 1), 7.0)

    async def _respect_rate_limit(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            wait_time = self._retry_delay_seconds - (now - self._last_request_at)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request_at = time.monotonic()

    async def _fetch_teams(self, client: httpx.AsyncClient, league_meta: dict, season_year: int) -> list[Team]:
        payload = await self._fetch_json(client, "/teams", params={"league": league_meta["id"], "season": season_year})
        teams: list[Team] = []
        for item in payload.get("response", []):
            team = item.get("team", {})
            teams.append(
                Team(
                    provider_id=str(team["id"]),
                    league_code=league_meta["code"],
                    season_year=season_year,
                    name=team["name"],
                    short_name=(team.get("code") or team["name"][:3]).upper(),
                    country=team.get("country") or league_meta["country"],
                )
            )
        return teams

    async def _fetch_player_leaders(self, client: httpx.AsyncClient, league_id: int, season_year: int) -> list[dict]:
        scorers = await self._fetch_json(client, "/players/topscorers", params={"league": league_id, "season": season_year})
        assisters = await self._fetch_json(client, "/players/topassists", params={"league": league_id, "season": season_year})
        combined = []
        combined.extend(scorers.get("response", []))
        combined.extend(assisters.get("response", []))
        return combined

    async def _fetch_recent_fixtures(self, client: httpx.AsyncClient, league_id: int, season_year: int) -> dict:
        end_date = datetime.now(UTC).date()
        start_date = end_date.replace(day=1)
        return await self._fetch_json(
            client,
            "/fixtures",
            params={
                "league": league_id,
                "season": season_year,
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
            },
        )

    def _map_team_rows(self, league_meta: dict, season_year: int, payload: dict) -> list[TeamPerformanceRow]:
        standings_groups = payload.get("response", [])
        if not standings_groups:
            return []
        raw_rows = standings_groups[0].get("league", {}).get("standings", [[]])[0]
        now = datetime.now(UTC)
        rows: list[TeamPerformanceRow] = []
        for row in raw_rows:
            team = row["team"]
            all_stats = row["all"]
            home_stats = row["home"]
            away_stats = row["away"]
            rows.append(
                TeamPerformanceRow(
                    league_code=league_meta["code"],
                    season_year=season_year,
                    team_name=team["name"],
                    matches_played=all_stats["played"],
                    wins=all_stats["win"],
                    draws=all_stats["draw"],
                    losses=all_stats["lose"],
                    goals_for=all_stats["goals"]["for"],
                    goals_against=all_stats["goals"]["against"],
                    points=row["points"],
                    form_points_last_5=_form_points(row.get("form")),
                    home_points=home_stats["win"] * 3 + home_stats["draw"],
                    away_points=away_stats["win"] * 3 + away_stats["draw"],
                    expected_goals_avg=0.0,
                    updated_at=now,
                )
            )
        return rows

    def _map_matches(self, league_code: str, season_year: int, payload: dict) -> list[Match]:
        output: list[Match] = []
        for item in payload.get("response", []):
            fixture = item["fixture"]
            output.append(
                Match(
                    provider_id=str(fixture["id"]),
                    league_code=league_code,
                    season_year=season_year,
                    match_date=datetime.fromisoformat(fixture["date"].replace("Z", "+00:00")),
                    status=fixture["status"]["short"],
                    home_team_provider_id=str(item["teams"]["home"]["id"]),
                    away_team_provider_id=str(item["teams"]["away"]["id"]),
                    home_score=item.get("goals", {}).get("home") or 0,
                    away_score=item.get("goals", {}).get("away") or 0,
                )
            )
        return output

    def _map_players_and_rows(
        self,
        league_code: str,
        season_year: int,
        payload_items: list[dict],
    ) -> tuple[list[Player], list[PlayerConsistencyRow]]:
        players: list[Player] = []
        rows: list[PlayerConsistencyRow] = []
        now = datetime.now(UTC)
        for item in payload_items:
            player_raw = item.get("player", {})
            statistics = item.get("statistics", [])
            if not statistics:
                continue
            stat = statistics[0]
            team = stat.get("team", {})
            games = stat.get("games", {})
            goals = stat.get("goals", {})
            player = Player(
                provider_id=str(player_raw["id"]),
                team_provider_id=str(team["id"]),
                name=player_raw["name"],
                position=games.get("position") or "N/A",
                nationality=player_raw.get("nationality") or "Unknown",
            )
            players.append(player)

            rating = _to_float(games.get("rating"))
            appearances = games.get("appearences") or 0
            lineups = games.get("lineups") or 0
            minutes = games.get("minutes") or 0
            consistency_score = round((rating or 0.0) * 10 * (0.5 + min(lineups / max(appearances, 1), 1.0) / 2), 2)
            rows.append(
                PlayerConsistencyRow(
                    league_code=league_code,
                    season_year=season_year,
                    team_name=team.get("name") or "Unknown",
                    player_name=player_raw["name"],
                    position=games.get("position") or "N/A",
                    matches_played=appearances,
                    minutes_played=minutes,
                    goals=goals.get("total") or 0,
                    assists=goals.get("assists") or 0,
                    average_rating=round(rating or 0.0, 2),
                    rating_stddev=0.0,
                    consistency_score=consistency_score,
                    updated_at=now,
                )
            )
        return players, rows

    def _map_injuries(self, payload: dict) -> list[InjuryRecord]:
        output: list[InjuryRecord] = []
        for item in payload.get("response", []):
            player = item.get("player", {})
            fixture = item.get("fixture", {})
            updated_at = fixture.get("date") or datetime.now(UTC).isoformat()
            output.append(
                InjuryRecord(
                    player_provider_id=str(player.get("id")),
                    status=player.get("type") or "injured",
                    detail=player.get("reason") or "Reported by API-Football",
                    updated_at=datetime.fromisoformat(updated_at.replace("Z", "+00:00")),
                )
            )
        return output


class _ExistingClientContext:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def _form_points(form: str | None) -> int:
    if not form:
        return 0
    mapping = {"W": 3, "D": 1, "L": 0}
    return sum(mapping.get(char, 0) for char in form[-5:])


def _to_float(value: str | float | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _dedupe_by_provider_id(items: list, attr: str = "provider_id") -> list:
    unique: dict[str, object] = {}
    for item in items:
        unique[str(getattr(item, attr))] = item
    return list(unique.values())

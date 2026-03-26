from __future__ import annotations

from datetime import UTC, datetime, timedelta

from soccer_analytics.domain import (
    InjuryRecord,
    League,
    Match,
    MatchStat,
    PipelineBundle,
    Player,
    PlayerMatchStat,
    Season,
    Team,
)
from soccer_analytics.ingestion.providers.base import SportsDataProvider


class MockSportsDataProvider(SportsDataProvider):
    name = "mock"

    async def fetch_bundle(self, league_code: str, season_year: int) -> PipelineBundle:
        pulled_at = datetime.now(UTC)
        league = League(provider_id="league-epl", code=league_code, name="Premier League", country="England")
        season = Season(
            provider_id=f"{league_code}-{season_year}",
            league_code=league_code,
            year=season_year,
            is_current=True,
        )

        teams = [
            Team(provider_id="ars", league_code=league_code, season_year=season_year, name="Arsenal", short_name="ARS", country="England"),
            Team(provider_id="liv", league_code=league_code, season_year=season_year, name="Liverpool", short_name="LIV", country="England"),
            Team(provider_id="mci", league_code=league_code, season_year=season_year, name="Manchester City", short_name="MCI", country="England"),
        ]

        players = [
            Player(provider_id="saka", team_provider_id="ars", name="Bukayo Saka", position="RW", nationality="England"),
            Player(provider_id="odegaard", team_provider_id="ars", name="Martin Odegaard", position="AM", nationality="Norway"),
            Player(provider_id="salah", team_provider_id="liv", name="Mohamed Salah", position="RW", nationality="Egypt"),
            Player(provider_id="haaland", team_provider_id="mci", name="Erling Haaland", position="ST", nationality="Norway"),
        ]

        now = datetime.now(UTC)
        matches = [
            Match(provider_id="match-1", league_code=league_code, season_year=season_year, match_date=now - timedelta(days=10), status="finished", home_team_provider_id="ars", away_team_provider_id="liv", home_score=2, away_score=1),
            Match(provider_id="match-2", league_code=league_code, season_year=season_year, match_date=now - timedelta(days=7), status="finished", home_team_provider_id="mci", away_team_provider_id="ars", home_score=1, away_score=1),
            Match(provider_id="match-3", league_code=league_code, season_year=season_year, match_date=now - timedelta(days=3), status="finished", home_team_provider_id="liv", away_team_provider_id="mci", home_score=0, away_score=3),
        ]

        match_stats = [
            MatchStat(match_provider_id="match-1", team_provider_id="ars", possession_pct=54.0, shots=15, shots_on_target=6, expected_goals=1.9),
            MatchStat(match_provider_id="match-1", team_provider_id="liv", possession_pct=46.0, shots=11, shots_on_target=4, expected_goals=1.2),
            MatchStat(match_provider_id="match-2", team_provider_id="mci", possession_pct=61.0, shots=14, shots_on_target=5, expected_goals=1.7),
            MatchStat(match_provider_id="match-2", team_provider_id="ars", possession_pct=39.0, shots=9, shots_on_target=3, expected_goals=1.0),
            MatchStat(match_provider_id="match-3", team_provider_id="liv", possession_pct=48.0, shots=10, shots_on_target=2, expected_goals=0.8),
            MatchStat(match_provider_id="match-3", team_provider_id="mci", possession_pct=52.0, shots=16, shots_on_target=8, expected_goals=2.5),
        ]

        player_match_stats = [
            PlayerMatchStat(match_provider_id="match-1", player_provider_id="saka", team_provider_id="ars", minutes_played=90, goals=1, assists=0, rating=7.8, passes_completed=31),
            PlayerMatchStat(match_provider_id="match-1", player_provider_id="salah", team_provider_id="liv", minutes_played=90, goals=1, assists=0, rating=7.2, passes_completed=24),
            PlayerMatchStat(match_provider_id="match-2", player_provider_id="odegaard", team_provider_id="ars", minutes_played=89, goals=0, assists=1, rating=7.4, passes_completed=42),
            PlayerMatchStat(match_provider_id="match-2", player_provider_id="haaland", team_provider_id="mci", minutes_played=90, goals=1, assists=0, rating=7.6, passes_completed=18),
            PlayerMatchStat(match_provider_id="match-3", player_provider_id="salah", team_provider_id="liv", minutes_played=90, goals=0, assists=0, rating=6.5, passes_completed=22),
            PlayerMatchStat(match_provider_id="match-3", player_provider_id="haaland", team_provider_id="mci", minutes_played=90, goals=2, assists=1, rating=9.1, passes_completed=16),
        ]

        injuries = [
            InjuryRecord(player_provider_id="saka", status="available", detail="No current injury", updated_at=pulled_at),
            InjuryRecord(player_provider_id="haaland", status="questionable", detail="Minor knock", updated_at=pulled_at),
        ]

        return PipelineBundle(
            leagues=[league],
            seasons=[season],
            teams=teams,
            players=players,
            matches=matches,
            match_stats=match_stats,
            player_match_stats=player_match_stats,
            injuries=injuries,
            pulled_at=pulled_at,
            source_name=self.name,
        )

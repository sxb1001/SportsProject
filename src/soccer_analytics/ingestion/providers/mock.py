from __future__ import annotations

from datetime import UTC, datetime, timedelta

from soccer_analytics.domain import (
    InjuryRecord,
    League,
    Match,
    MatchStat,
    PipelineBundle,
    Player,
    PlayerHeatmapCell,
    PlayerMatchStat,
    Season,
    Team,
)
from soccer_analytics.ingestion.providers.base import SportsDataProvider


LEAGUE_DEFINITIONS = [
    {
        "code": "EPL",
        "name": "Premier League",
        "country": "England",
        "teams": [
            "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Burnley",
            "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool", "Luton Town",
            "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest",
            "Sheffield United", "Tottenham Hotspur", "West Ham United", "Wolverhampton",
        ],
    },
    {
        "code": "L1",
        "name": "Ligue 1",
        "country": "France",
        "teams": [
            "Brest", "Clermont", "Le Havre", "Lens", "Lille", "Lorient", "Lyon", "Marseille",
            "Metz", "Monaco", "Montpellier", "Nantes", "Nice", "Paris Saint-Germain",
            "Reims", "Rennes", "Strasbourg", "Toulouse",
        ],
    },
    {
        "code": "LL",
        "name": "La Liga",
        "country": "Spain",
        "teams": [
            "Alaves", "Almeria", "Athletic Club", "Atletico Madrid", "Barcelona", "Cadiz",
            "Celta Vigo", "Getafe", "Girona", "Granada", "Las Palmas", "Mallorca",
            "Osasuna", "Rayo Vallecano", "Real Betis", "Real Madrid", "Real Sociedad",
            "Sevilla", "Valencia", "Villarreal",
        ],
    },
    {
        "code": "BL1",
        "name": "Bundesliga",
        "country": "Germany",
        "teams": [
            "Augsburg", "Bayer Leverkusen", "Bayern Munich", "Bochum", "Borussia Dortmund",
            "Borussia Monchengladbach", "Darmstadt", "Eintracht Frankfurt", "Freiburg",
            "Heidenheim", "Hoffenheim", "Koln", "Mainz", "RB Leipzig", "Stuttgart",
            "Union Berlin", "Werder Bremen", "Wolfsburg",
        ],
    },
    {
        "code": "SA",
        "name": "Serie A",
        "country": "Italy",
        "teams": [
            "AC Milan", "Atalanta", "Bologna", "Cagliari", "Empoli", "Fiorentina",
            "Frosinone", "Genoa", "Hellas Verona", "Inter Milan", "Juventus", "Lazio",
            "Lecce", "Monza", "Napoli", "Roma", "Salernitana", "Sassuolo", "Torino", "Udinese",
        ],
    },
]

POSITION_CYCLE = ["ST", "RW", "LW"]


class MockSportsDataProvider(SportsDataProvider):
    name = "mock"

    async def fetch_bundle(self, league_code: str, season_year: int) -> PipelineBundle:
        pulled_at = datetime.now(UTC)
        leagues = [
            League(
                provider_id=f"league-{league['code'].lower()}",
                code=league["code"],
                name=league["name"],
                country=league["country"],
            )
            for league in LEAGUE_DEFINITIONS
        ]
        seasons = [
            Season(
                provider_id=f"{league['code']}-{season_year}",
                league_code=league["code"],
                year=season_year,
                is_current=True,
            )
            for league in LEAGUE_DEFINITIONS
        ]

        teams: list[Team] = []
        players: list[Player] = []
        matches: list[Match] = []
        match_stats: list[MatchStat] = []
        player_match_stats: list[PlayerMatchStat] = []
        player_heatmap_cells: list[PlayerHeatmapCell] = []
        injuries: list[InjuryRecord] = []

        for league_index, league in enumerate(LEAGUE_DEFINITIONS):
            league_teams: list[Team] = []
            for team_index, team_name in enumerate(league["teams"]):
                provider_id = f"{league['code'].lower()}-{_slugify(team_name)}"
                team = Team(
                    provider_id=provider_id,
                    league_code=league["code"],
                    season_year=season_year,
                    name=team_name,
                    short_name=_short_name(team_name),
                    country=league["country"],
                )
                teams.append(team)
                league_teams.append(team)

                for player_offset in range(2):
                    player_id = f"{provider_id}-p{player_offset + 1}"
                    players.append(
                        Player(
                            provider_id=player_id,
                            team_provider_id=provider_id,
                            name=f"{team_name} Player {player_offset + 1}",
                            position=POSITION_CYCLE[(team_index + player_offset) % len(POSITION_CYCLE)],
                            nationality=league["country"],
                        )
                    )

                    injuries.append(
                        InjuryRecord(
                            player_provider_id=player_id,
                            status="available" if (team_index + player_offset) % 7 else "questionable",
                            detail="Load-managed in demo feed" if (team_index + player_offset) % 7 == 0 else "No current injury",
                            updated_at=pulled_at,
                        )
                    )

            league_matches, league_match_stats, league_player_stats, league_heatmap_cells = self._build_league_schedule(
                league_index=league_index,
                season_year=season_year,
                league_code=league["code"],
                teams=league_teams,
                players=players,
            )
            matches.extend(league_matches)
            match_stats.extend(league_match_stats)
            player_match_stats.extend(league_player_stats)
            player_heatmap_cells.extend(league_heatmap_cells)

        return PipelineBundle(
            leagues=leagues,
            seasons=seasons,
            teams=teams,
            players=players,
            matches=matches,
            match_stats=match_stats,
            player_match_stats=player_match_stats,
            player_heatmap_cells=player_heatmap_cells,
            injuries=injuries,
            pulled_at=pulled_at,
            source_name=self.name,
        )

    def _build_league_schedule(
        self,
        league_index: int,
        season_year: int,
        league_code: str,
        teams: list[Team],
        players: list[Player],
    ) -> tuple[list[Match], list[MatchStat], list[PlayerMatchStat], list[PlayerHeatmapCell]]:
        team_players = {team.provider_id: [player for player in players if player.team_provider_id == team.provider_id] for team in teams}
        matches: list[Match] = []
        match_stats: list[MatchStat] = []
        player_stats: list[PlayerMatchStat] = []
        heatmap_cells: list[PlayerHeatmapCell] = []

        for round_index in range(3):
            rotated = teams[round_index:] + teams[:round_index]
            pair_count = len(rotated) // 2
            for pair_index in range(pair_count):
                home_team = rotated[pair_index]
                away_team = rotated[-(pair_index + 1)]
                if (round_index + pair_index) % 2:
                    home_team, away_team = away_team, home_team

                match_id = f"{league_code.lower()}-{season_year}-r{round_index + 1}-m{pair_index + 1}"
                match_date = datetime.now(UTC) - timedelta(days=(league_index * 4 + round_index) * 3 + pair_index)
                home_score = (pair_index + league_index + round_index + len(home_team.name)) % 4
                away_score = (pair_index * 2 + league_index + len(away_team.name)) % 3

                matches.append(
                    Match(
                        provider_id=match_id,
                        league_code=league_code,
                        season_year=season_year,
                        match_date=match_date,
                        status="finished",
                        home_team_provider_id=home_team.provider_id,
                        away_team_provider_id=away_team.provider_id,
                        home_score=home_score,
                        away_score=away_score,
                    )
                )

                for side_index, team in enumerate((home_team, away_team)):
                    expected_goals = round(0.8 + ((pair_index + round_index + side_index + len(team.name)) % 7) * 0.25, 2)
                    match_stats.append(
                        MatchStat(
                            match_provider_id=match_id,
                            team_provider_id=team.provider_id,
                            possession_pct=round(44 + ((pair_index * 3 + side_index * 7 + len(team.name)) % 15), 1),
                            shots=8 + ((pair_index + side_index + round_index + len(team.name)) % 10),
                            shots_on_target=3 + ((pair_index + side_index + len(team.name)) % 5),
                            expected_goals=expected_goals,
                        )
                    )

                    team_score = home_score if team.provider_id == home_team.provider_id else away_score
                    for player_index, player in enumerate(team_players[team.provider_id]):
                        goals = 1 if player_index == 0 and team_score > 0 else 0
                        assists = 1 if player_index == 1 and team_score > 1 else 0
                        rating = round(6.4 + ((pair_index + round_index + player_index + len(player.name)) % 26) / 10, 1)
                        passes_completed = 18 + ((pair_index * 4 + player_index * 6 + len(team.name)) % 37)

                        player_stats.append(
                            PlayerMatchStat(
                                match_provider_id=match_id,
                                player_provider_id=player.provider_id,
                                team_provider_id=team.provider_id,
                                minutes_played=90 - player_index,
                                goals=goals,
                                assists=assists,
                                rating=rating,
                                passes_completed=passes_completed,
                            )
                        )

                        for zone_row in range(4):
                            for zone_col in range(6):
                                heatmap_cells.append(
                                    PlayerHeatmapCell(
                                        match_provider_id=match_id,
                                        player_provider_id=player.provider_id,
                                        team_provider_id=team.provider_id,
                                        match_date=match_date,
                                        zone_row=zone_row,
                                        zone_col=zone_col,
                                        touch_count=_touch_count(
                                            player.provider_id,
                                            match_id,
                                            zone_row,
                                            zone_col,
                                            player_index,
                                        ),
                                    )
                                )

        return matches, match_stats, player_stats, heatmap_cells


def _slugify(value: str) -> str:
    return value.lower().replace(" ", "-").replace(".", "").replace("'", "")


def _short_name(value: str) -> str:
    parts = value.replace("-", " ").split()
    if len(parts) == 1:
        return value[:3].upper()
    return "".join(part[0] for part in parts[:3]).upper()


def _touch_count(player_id: str, match_id: str, zone_row: int, zone_col: int, player_index: int) -> int:
    seed = sum(ord(char) for char in f"{player_id}:{match_id}")
    return 2 + ((seed + zone_row * 5 + zone_col * 3 + player_index * 7) % 16)

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from math import sqrt

from soccer_analytics.domain import PipelineBundle, PlayerConsistencyRow, TeamPerformanceRow


def build_team_performance_rows(bundle: PipelineBundle) -> list[TeamPerformanceRow]:
    team_lookup = {team.provider_id: team for team in bundle.teams}
    league_lookup = {team.provider_id: team.league_code for team in bundle.teams}
    season_lookup = {team.provider_id: team.season_year for team in bundle.teams}
    stats_by_team = defaultdict(
        lambda: {
            "matches_played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "points": 0,
            "results": [],
            "home_points": 0,
            "away_points": 0,
            "expected_goals": [],
        }
    )

    for match in sorted(bundle.matches, key=lambda item: item.match_date):
        home = stats_by_team[match.home_team_provider_id]
        away = stats_by_team[match.away_team_provider_id]
        home["matches_played"] += 1
        away["matches_played"] += 1
        home["goals_for"] += match.home_score
        home["goals_against"] += match.away_score
        away["goals_for"] += match.away_score
        away["goals_against"] += match.home_score

        if match.home_score > match.away_score:
            _apply_result(home, "win", location="home")
            _apply_result(away, "loss", location="away")
        elif match.home_score < match.away_score:
            _apply_result(home, "loss", location="home")
            _apply_result(away, "win", location="away")
        else:
            _apply_result(home, "draw", location="home")
            _apply_result(away, "draw", location="away")

    for match_stat in bundle.match_stats:
        stats_by_team[match_stat.team_provider_id]["expected_goals"].append(match_stat.expected_goals)

    updated_at = datetime.now(UTC)
    rows: list[TeamPerformanceRow] = []
    for team_id, stats in stats_by_team.items():
        recent_results = stats["results"][-5:]
        rows.append(
            TeamPerformanceRow(
                league_code=league_lookup[team_id],
                season_year=season_lookup[team_id],
                team_name=team_lookup[team_id].name,
                matches_played=stats["matches_played"],
                wins=stats["wins"],
                draws=stats["draws"],
                losses=stats["losses"],
                goals_for=stats["goals_for"],
                goals_against=stats["goals_against"],
                points=stats["points"],
                form_points_last_5=sum(recent_results),
                home_points=stats["home_points"],
                away_points=stats["away_points"],
                expected_goals_avg=round(sum(stats["expected_goals"]) / max(len(stats["expected_goals"]), 1), 2),
                updated_at=updated_at,
            )
        )
    return rows


def _apply_result(bucket: dict, result: str, location: str) -> None:
    points = 3 if result == "win" else 1 if result == "draw" else 0
    if result == "win":
        bucket["wins"] += 1
    elif result == "draw":
        bucket["draws"] += 1
    else:
        bucket["losses"] += 1
    bucket["points"] += points
    bucket["results"].append(points)
    key = "home_points" if location == "home" else "away_points"
    bucket[key] += points


def build_player_consistency_rows(bundle: PipelineBundle) -> list[PlayerConsistencyRow]:
    player_lookup = {player.provider_id: player for player in bundle.players}
    team_lookup = {team.provider_id: team for team in bundle.teams}
    stats_by_player = defaultdict(
        lambda: {
            "matches_played": 0,
            "minutes_played": 0,
            "goals": 0,
            "assists": 0,
            "ratings": [],
        }
    )

    for row in bundle.player_match_stats:
        bucket = stats_by_player[row.player_provider_id]
        bucket["matches_played"] += 1
        bucket["minutes_played"] += row.minutes_played
        bucket["goals"] += row.goals
        bucket["assists"] += row.assists
        bucket["ratings"].append(row.rating)

    updated_at = datetime.now(UTC)
    output: list[PlayerConsistencyRow] = []
    for player_id, stats in stats_by_player.items():
        ratings = stats["ratings"]
        avg = sum(ratings) / len(ratings)
        variance = sum((rating - avg) ** 2 for rating in ratings) / len(ratings)
        stddev = sqrt(variance)
        player = player_lookup[player_id]
        team = team_lookup[player.team_provider_id]
        output.append(
            PlayerConsistencyRow(
                league_code=team.league_code,
                season_year=team.season_year,
                team_name=team.name,
                player_name=player.name,
                position=player.position,
                matches_played=stats["matches_played"],
                minutes_played=stats["minutes_played"],
                goals=stats["goals"],
                assists=stats["assists"],
                average_rating=round(avg, 2),
                rating_stddev=round(stddev, 2),
                consistency_score=round(max(avg * 10 - stddev * 5, 0), 2),
                updated_at=updated_at,
            )
        )
    return output

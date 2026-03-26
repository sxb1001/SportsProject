import asyncio

from soccer_analytics.ingestion.providers.mock import MockSportsDataProvider
from soccer_analytics.transforms.metrics import build_player_consistency_rows, build_team_performance_rows


def test_team_performance_metrics():
    bundle = asyncio.run(MockSportsDataProvider().fetch_bundle("EPL", 2024))
    rows = build_team_performance_rows(bundle)
    by_team = {row.team_name: row for row in rows}

    assert by_team["Manchester City"].points == 4
    assert by_team["Arsenal"].matches_played == 2
    assert by_team["Liverpool"].goals_for == 1


def test_player_consistency_metrics():
    bundle = asyncio.run(MockSportsDataProvider().fetch_bundle("EPL", 2024))
    rows = build_player_consistency_rows(bundle)
    by_player = {row.player_name: row for row in rows}

    assert by_player["Erling Haaland"].goals == 3
    assert by_player["Mohamed Salah"].matches_played == 2
    assert by_player["Erling Haaland"].consistency_score > by_player["Mohamed Salah"].consistency_score

import asyncio

from soccer_analytics.ingestion.providers.mock import MockSportsDataProvider
from soccer_analytics.transforms.metrics import build_player_consistency_rows, build_team_performance_rows


def test_team_performance_metrics():
    bundle = asyncio.run(MockSportsDataProvider().fetch_bundle("TOP5", 2024))
    rows = build_team_performance_rows(bundle)
    by_team = {row.team_name: row for row in rows}

    assert len(rows) == 96
    assert by_team["Manchester City"].league_code == "EPL"
    assert by_team["Paris Saint-Germain"].league_code == "L1"
    assert by_team["Real Madrid"].league_code == "LL"
    assert by_team["Bayern Munich"].league_code == "BL1"
    assert by_team["Inter Milan"].league_code == "SA"


def test_player_consistency_metrics():
    bundle = asyncio.run(MockSportsDataProvider().fetch_bundle("TOP5", 2024))
    rows = build_player_consistency_rows(bundle)
    by_player = {row.player_name: row for row in rows}

    assert len(rows) == 192
    assert by_player["Arsenal Player 1"].team_name == "Arsenal"
    assert by_player["Paris Saint-Germain Player 1"].team_name == "Paris Saint-Germain"
    assert by_player["Arsenal Player 1"].matches_played >= 1

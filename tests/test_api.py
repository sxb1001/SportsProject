from fastapi.testclient import TestClient

from soccer_analytics.api.main import app
from soccer_analytics.storage.database import init_db


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage_serves_browser_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "Soccer Analytics Dashboard" in response.text
    assert "Refresh Demo Data" in response.text


def test_refresh_and_analytics_endpoints():
    init_db()

    refresh_response = client.post("/pipeline/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json()["status"] == "completed"

    team_response = client.get("/analytics/team-performance")
    assert team_response.status_code == 200
    assert len(team_response.json()) >= 1

    player_response = client.get("/analytics/player-consistency?minimum_minutes=80")
    assert player_response.status_code == 200
    assert len(player_response.json()) >= 1

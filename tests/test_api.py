import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_soccer_analytics.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["RAW_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SPORTS_PROVIDER"] = "mock"

import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_soccer_analytics.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["RAW_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SPORTS_PROVIDER"] = "mock"

from fastapi.testclient import TestClient

from soccer_analytics.api.dependencies import get_pipeline_service
from soccer_analytics.api.main import app
from soccer_analytics.config import get_settings
from soccer_analytics.ingestion.providers.mock import MockSportsDataProvider
from soccer_analytics.ingestion.service import PipelineService
from soccer_analytics.storage.database import SessionLocal, init_db
from soccer_analytics.storage.repository import AnalyticsRepository
from soccer_analytics.storage.s3_store import RawSnapshotStore


client = TestClient(app)


def override_pipeline_service() -> PipelineService:
    session = SessionLocal()
    repository = AnalyticsRepository(session)
    settings = get_settings()
    return PipelineService(
        settings=settings,
        repository=repository,
        raw_store=RawSnapshotStore(settings),
        provider=MockSportsDataProvider(),
    )


app.dependency_overrides[get_pipeline_service] = override_pipeline_service


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
    assert len(team_response.json()) == 96

    player_response = client.get("/analytics/player-consistency?minimum_minutes=80")
    assert player_response.status_code == 200
    assert len(player_response.json()) == 192

    heatmap_response = client.get("/analytics/player-heatmaps?player_provider_id=epl-arsenal-p1&last_n_games=3")
    assert heatmap_response.status_code == 200
    payload = heatmap_response.json()
    assert payload["player_provider_id"] == "epl-arsenal-p1"
    assert len(payload["matches"]) >= 1
    assert len(payload["rolling_cells"]) == 24

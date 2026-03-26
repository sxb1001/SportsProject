# Soccer Analytics Pipeline

Portfolio-ready soccer analytics platform with:

- Near-real-time ingestion from API-Football for the top European first divisions
- Raw snapshot storage in S3
- PostgreSQL warehouse tables plus analytics marts
- FastAPI backend for metadata, pipeline status, and curated analytics
- AWS Lambda deployment target with Docker parity
- Power BI-ready datasets and API contracts

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
docker compose up --build
pytest
```

If editable install has issues on a Windows/OneDrive path, install the dependencies directly and run with
`PYTHONPATH=src`:

```powershell
$env:PYTHONPATH="src"
python -m pip install boto3 fastapi httpx mangum "psycopg[binary]" pydantic-settings python-dateutil sqlalchemy uvicorn mypy pytest pytest-asyncio ruff
python -m pytest
```

## Run the API

Because this project uses a `src/` layout, start the API with one of these commands from the repo root:

```powershell
$env:PYTHONPATH="src"
python -m uvicorn soccer_analytics.api.main:app --host 127.0.0.1 --port 8000
```

or:

```powershell
python run_api.py
```

To run one daily ingestion manually from the repo root:

```powershell
$env:PYTHONPATH="src"
python refresh_pipeline.py
```

## Real provider setup

1. Create an API-Football account and get a free API key.
2. Copy `.env.example` to `.env`.
3. Set `SPORTS_API_KEY` in `.env`.
4. Start the API and trigger `POST /pipeline/refresh` or use the browser refresh button.

Notes:

- The default runtime provider is `api_football`.
- The provider is throttled to stay under the free-tier per-minute limit by default.
- The repo is now set up for a once-daily refresh cadence instead of every 15 minutes.
- The free API-Football plan is still the main constraint for full top-5-league player coverage, so a single refresh may take several minutes.
- True player XY heatmaps are not available from the free provider, so the dashboard marks that feature as unavailable until an event-coordinate provider is added.

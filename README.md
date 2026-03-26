# Soccer Analytics Pipeline

Portfolio-ready soccer analytics platform with:

- Near-real-time ingestion from a pluggable public sports API
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

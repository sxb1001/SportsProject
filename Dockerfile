FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests

RUN pip install --upgrade pip && pip install .

CMD ["uvicorn", "soccer_analytics.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

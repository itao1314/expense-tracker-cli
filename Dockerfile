FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web

RUN python -m pip install --upgrade pip && \
    python -m pip install ".[api]"

USER app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "expense_tracker.api:app", "--host", "0.0.0.0", "--port", "8000"]

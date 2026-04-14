# Expense Tracker CLI

A small terminal-first expense tracker for developers who want to log spending quickly.

## Features

- `expense add 50 lunch`
- `expense list`
- `expense report`
- `expense export expenses.csv`
- `expense delete 3`
- `expense edit 3 --amount 24 --description dinner --category food`
- Local SQLite storage with automatic setup

## Install

```bash
python3 -m pip install .
```

Install build tooling:

```bash
python3 -m pip install ".[build]"
```

Install API tooling:

```bash
python3 -m pip install ".[api]"
```

## Usage

Add an expense:

```bash
expense add 50 lunch
expense add 12.50 coffee beans --category groceries
```

List expenses:

```bash
expense list
expense list --limit 10
```

Show a report:

```bash
expense report
expense report --month 2026-04
```

`expense report` now includes an overall category totals section, with categories sorted by total spend descending.

Export expenses:

```bash
expense export expenses.csv
```

Delete an expense:

```bash
expense delete 3
```

Edit an expense:

```bash
expense edit 3 --amount 24 --description dinner --category food
expense edit 3 --category groceries
```

## API Server

Run the FastAPI server with:

```bash
python3 -m uvicorn expense_tracker.api:app --reload
```

If you are running from source without installing the package first, include `src` on `PYTHONPATH`:

```bash
PYTHONPATH=src python3 -m uvicorn expense_tracker.api:app --reload
```

Available endpoints:

- `GET /expenses`
- `POST /expenses`
- `DELETE /expenses/{id}`
- `PATCH /expenses/{id}`
- `GET /report`

## Docker

Build the container image:

```bash
docker build -t expense-tracker-api .
```

Run the FastAPI app on port `8000`:

```bash
docker run --rm -p 8000:8000 expense-tracker-api
```

If you want the database to persist outside the container, mount a host path and point `EXPENSE_DB_PATH` at it:

```bash
docker run --rm \
  -p 8000:8000 \
  -e EXPENSE_DB_PATH=/data/expenses.db \
  -v "$(pwd)/.data:/data" \
  expense-tracker-api
```

## Storage

By default the database is created at:

- macOS: `~/Library/Application Support/expense-tracker/expenses.db`
- Linux/XDG: `$XDG_DATA_HOME/expense-tracker/expenses.db`
- Fallback: `~/.expense-tracker/expenses.db`

Override the location with:

```bash
export EXPENSE_DB_PATH=/path/to/expenses.db
```

## Build Executable

Build a single-file binary with PyInstaller:

```bash
make build
```

The binary will be written to:

```bash
dist/expense
```

If you want to rebuild from a clean state:

```bash
make clean
make build
```

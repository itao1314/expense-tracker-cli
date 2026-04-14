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

## Storage

By default the database is created at:

- macOS: `~/Library/Application Support/expense-tracker/expenses.db`
- Linux/XDG: `$XDG_DATA_HOME/expense-tracker/expenses.db`
- Fallback: `~/.expense-tracker/expenses.db`

Override the location with:

```bash
export EXPENSE_DB_PATH=/path/to/expenses.db
```

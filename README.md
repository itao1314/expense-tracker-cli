# Expense Tracker CLI

A small terminal-first expense tracker for developers who want to log spending quickly.

## Install

```bash
python3 -m pip install .
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

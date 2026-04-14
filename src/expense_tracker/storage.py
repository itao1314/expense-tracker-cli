from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


def default_db_path() -> Path:
    override = os.getenv("EXPENSE_DB_PATH")
    if override:
        return Path(override).expanduser()

    home = Path.home()
    if os.name == "posix" and "darwin" in os.sys.platform:
        return home / "Library" / "Application Support" / "expense-tracker" / "expenses.db"

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home).expanduser() / "expense-tracker" / "expenses.db"

    return home / ".expense-tracker" / "expenses.db"


@dataclass(frozen=True)
class Expense:
    id: int
    amount: Decimal
    description: str
    category: str
    created_at: str


def normalize_amount(value: str | float) -> Decimal:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Amount must be a valid number.") from exc

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ExpenseStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def add_expense(self, amount: Decimal, description: str, category: str) -> Expense:
        timestamp = datetime.now().isoformat(timespec="seconds")
        cursor = self.connection.execute(
            """
            INSERT INTO expenses (amount, description, category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (str(amount), description, category, timestamp),
        )
        self.connection.commit()
        return Expense(
            id=int(cursor.lastrowid),
            amount=amount,
            description=description,
            category=category,
            created_at=timestamp,
        )

    def list_expenses(self, limit: int | None = None) -> list[Expense]:
        query = """
            SELECT id, amount, description, category, created_at
            FROM expenses
            ORDER BY datetime(created_at) DESC, id DESC
        """
        params: tuple[int, ...] = ()
        if limit:
            query += " LIMIT ?"
            params = (limit,)

        rows = self.connection.execute(query, params).fetchall()
        return [
            Expense(
                id=row["id"],
                amount=Decimal(row["amount"]),
                description=row["description"],
                category=row["category"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def all_expenses(self) -> list[Expense]:
        return self.list_expenses(limit=None)

    def monthly_totals(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT substr(created_at, 1, 7) AS month, SUM(CAST(amount AS REAL)) AS total
            FROM expenses
            GROUP BY substr(created_at, 1, 7)
            ORDER BY month DESC
            """
        ).fetchall()

    def monthly_category_totals(self, month: str | None = None) -> list[sqlite3.Row]:
        query = """
            SELECT substr(created_at, 1, 7) AS month, category, SUM(CAST(amount AS REAL)) AS total
            FROM expenses
        """
        params: tuple[str, ...] = ()
        if month:
            query += " WHERE substr(created_at, 1, 7) = ?"
            params = (month,)

        query += """
            GROUP BY substr(created_at, 1, 7), category
            ORDER BY month DESC, total DESC, category ASC
        """
        return self.connection.execute(query, params).fetchall()

    def close(self) -> None:
        self.connection.close()

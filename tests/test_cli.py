from __future__ import annotations

import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from typer.testing import CliRunner

from expense_tracker.cli import app
from expense_tracker.storage import ExpenseStore


class DeleteCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "expenses.db"
        self.previous_db_path = os.environ.get("EXPENSE_DB_PATH")
        os.environ["EXPENSE_DB_PATH"] = str(self.db_path)

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("EXPENSE_DB_PATH", None)
        else:
            os.environ["EXPENSE_DB_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def test_delete_command_removes_expense(self) -> None:
        store = ExpenseStore(db_path=self.db_path)
        expense = store.add_expense(amount=Decimal("10.00"), description="coffee", category="food")
        store.close()

        result = self.runner.invoke(app, ["delete", str(expense.id)])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(f"Deleted expense #{expense.id}.", result.stdout)

        store = ExpenseStore(db_path=self.db_path)
        try:
            self.assertEqual(store.all_expenses(), [])
        finally:
            store.close()

    def test_delete_command_shows_friendly_error_for_missing_id(self) -> None:
        result = self.runner.invoke(app, ["delete", "999"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Expense with ID 999 was not found.", result.stdout)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from expense_tracker.storage import ExpenseStore, normalize_amount


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "expenses.db"
        self.store = ExpenseStore(db_path=self.db_path)

    def tearDown(self) -> None:
        self.store.close()
        self.temp_dir.cleanup()

    def test_normalize_amount_rounds_to_cents(self) -> None:
        self.assertEqual(normalize_amount("12.345"), Decimal("12.35"))

    def test_add_and_list_expenses(self) -> None:
        self.store.add_expense(Decimal("10.00"), "coffee", "food")
        self.store.add_expense(Decimal("25.50"), "book", "learning")

        expenses = self.store.list_expenses()

        self.assertEqual(len(expenses), 2)
        self.assertEqual(expenses[0].description, "book")
        self.assertEqual(expenses[1].description, "coffee")

    def test_monthly_reports_group_data(self) -> None:
        self.store.add_expense(Decimal("10.00"), "coffee", "food")
        self.store.add_expense(Decimal("15.00"), "lunch", "food")

        monthly = self.store.monthly_totals()
        categories = self.store.monthly_category_totals()

        self.assertEqual(len(monthly), 1)
        self.assertEqual(round(monthly[0]["total"], 2), 25.0)
        self.assertEqual(categories[0]["category"], "food")
        self.assertEqual(round(categories[0]["total"], 2), 25.0)

    def test_all_expenses_returns_every_record(self) -> None:
        self.store.add_expense(Decimal("10.00"), "coffee", "food")
        self.store.add_expense(Decimal("15.00"), "lunch", "food")

        expenses = self.store.all_expenses()

        self.assertEqual(len(expenses), 2)

    def test_delete_expense_removes_matching_record(self) -> None:
        expense = self.store.add_expense(Decimal("10.00"), "coffee", "food")

        deleted = self.store.delete_expense(expense.id)
        expenses = self.store.all_expenses()

        self.assertTrue(deleted)
        self.assertEqual(expenses, [])

    def test_delete_expense_returns_false_for_missing_id(self) -> None:
        deleted = self.store.delete_expense(999)

        self.assertFalse(deleted)


if __name__ == "__main__":
    unittest.main()

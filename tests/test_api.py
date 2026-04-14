from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi is not installed")
class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "expenses.db"
        self.previous_db_path = os.environ.get("EXPENSE_DB_PATH")
        os.environ["EXPENSE_DB_PATH"] = str(self.db_path)

        from expense_tracker.api import app

        self.client = TestClient(app)

    def tearDown(self) -> None:
        if self.previous_db_path is None:
            os.environ.pop("EXPENSE_DB_PATH", None)
        else:
            os.environ["EXPENSE_DB_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def test_post_and_get_expenses(self) -> None:
        create_response = self.client.post(
            "/expenses",
            json={"amount": "12.50", "description": "coffee", "category": "Food"},
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json()["amount"], "12.50")
        self.assertEqual(create_response.json()["category"], "food")

        list_response = self.client.get("/expenses")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]["description"], "coffee")

    def test_root_serves_web_ui(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Expense Tracker", response.text)

    def test_patch_expense(self) -> None:
        create_response = self.client.post(
            "/expenses",
            json={"amount": "12.50", "description": "coffee", "category": "food"},
        )
        expense_id = create_response.json()["id"]

        update_response = self.client.patch(
            f"/expenses/{expense_id}",
            json={"amount": "15.75", "category": "groceries"},
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["amount"], "15.75")
        self.assertEqual(update_response.json()["category"], "groceries")

    def test_delete_expense(self) -> None:
        create_response = self.client.post(
            "/expenses",
            json={"amount": "12.50", "description": "coffee", "category": "food"},
        )
        expense_id = create_response.json()["id"]

        delete_response = self.client.delete(f"/expenses/{expense_id}")

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(self.client.get("/expenses").json(), [])

    def test_report_returns_category_totals(self) -> None:
        self.client.post("/expenses", json={"amount": "5.00", "description": "coffee", "category": "food"})
        self.client.post("/expenses", json={"amount": "30.00", "description": "groceries", "category": "shopping"})
        self.client.post("/expenses", json={"amount": "15.00", "description": "lunch", "category": "food"})

        report_response = self.client.get("/report")

        self.assertEqual(report_response.status_code, 200)
        payload = report_response.json()
        self.assertEqual(payload["category_totals"][0]["category"], "shopping")
        self.assertEqual(payload["category_totals"][1]["category"], "food")


if __name__ == "__main__":
    unittest.main()

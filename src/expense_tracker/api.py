from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from .storage import Expense, ExpenseStore, normalize_amount

app = FastAPI(title="Expense Tracker API", version="1.0.0")
WEB_INDEX = Path(__file__).resolve().parents[2] / "web" / "index.html"


class ExpenseResponse(BaseModel):
    id: int
    amount: str
    description: str
    category: str
    created_at: str


class ExpenseCreateRequest(BaseModel):
    amount: str = Field(..., examples=["12.50"])
    description: str = Field(..., min_length=1)
    category: str = Field(default="uncategorized", min_length=1)


class ExpenseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: str | None = Field(default=None, examples=["15.00"])
    description: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1)


class CategoryTotal(BaseModel):
    category: str
    total: float


class MonthlyTotal(BaseModel):
    month: str
    total: float


class MonthlyCategoryBreakdown(BaseModel):
    month: str
    categories: list[CategoryTotal]


class ReportResponse(BaseModel):
    monthly_totals: list[MonthlyTotal]
    category_totals: list[CategoryTotal]
    category_breakdowns: list[MonthlyCategoryBreakdown]


def get_store() -> ExpenseStore:
    store = ExpenseStore()
    try:
        yield store
    finally:
        store.close()


StoreDep = Annotated[ExpenseStore, Depends(get_store)]


def serialize_expense(expense: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense.id,
        amount=f"{expense.amount:.2f}",
        description=expense.description,
        category=expense.category,
        created_at=expense.created_at,
    )


def parse_amount(value: str) -> Decimal:
    try:
        return normalize_amount(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


def normalize_category(value: str) -> str:
    category = value.strip().lower()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category is required.",
        )
    return category


def normalize_description(value: str) -> str:
    description = value.strip()
    if not description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Description is required.",
        )
    return description


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    if not WEB_INDEX.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Web UI not found.")
    return FileResponse(WEB_INDEX)


@app.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    store: StoreDep,
    limit: Annotated[int | None, Query(ge=1)] = None,
) -> list[ExpenseResponse]:
    expenses = store.list_expenses(limit=limit)
    return [serialize_expense(expense) for expense in expenses]


@app.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreateRequest, store: StoreDep) -> ExpenseResponse:
    expense = store.add_expense(
        amount=parse_amount(payload.amount),
        description=normalize_description(payload.description),
        category=normalize_category(payload.category),
    )
    return serialize_expense(expense)


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, store: StoreDep) -> Response:
    deleted = store.delete_expense(expense_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, payload: ExpenseUpdateRequest, store: StoreDep) -> ExpenseResponse:
    parsed_amount: Decimal | None = None
    description: str | None = None
    category: str | None = None

    if payload.amount is not None:
        parsed_amount = parse_amount(payload.amount)
    if payload.description is not None:
        description = normalize_description(payload.description)
    if payload.category is not None:
        category = normalize_category(payload.category)

    if parsed_amount is None and description is None and category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one field to update.",
        )

    updated = store.update_expense(
        expense_id,
        amount=parsed_amount,
        description=description,
        category=category,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

    expense = store.get_expense(expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    return serialize_expense(expense)


@app.get("/report", response_model=ReportResponse)
def get_report(
    store: StoreDep,
    month: str | None = None,
) -> ReportResponse:
    if month is not None:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Month must use YYYY-MM format.",
            ) from exc

    monthly_rows = store.monthly_totals()
    category_rows = store.monthly_category_totals(month=month)
    category_totals = store.category_totals(month=month)

    if month is not None and not category_rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No expenses found for {month}.")

    grouped: dict[str, list[CategoryTotal]] = {}
    for row in category_rows:
        grouped.setdefault(
            row["month"],
            [],
        ).append(CategoryTotal(category=row["category"], total=float(row["total"])))

    return ReportResponse(
        monthly_totals=[MonthlyTotal(month=row["month"], total=float(row["total"])) for row in monthly_rows],
        category_totals=[CategoryTotal(category=row["category"], total=float(row["total"])) for row in category_totals],
        category_breakdowns=[
            MonthlyCategoryBreakdown(month=month_key, categories=categories)
            for month_key, categories in grouped.items()
        ],
    )

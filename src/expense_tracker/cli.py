from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .storage import ExpenseStore, normalize_amount

app = typer.Typer(help="Track personal expenses from the terminal.")
console = Console()


def money(value: Decimal | float) -> str:
    return f"${Decimal(str(value)).quantize(Decimal('0.01'))}"


def get_store() -> ExpenseStore:
    return ExpenseStore()


@app.command()
def add(
    amount: str = typer.Argument(..., help="Expense amount."),
    description: list[str] = typer.Argument(..., help="Expense description."),
    category: str = typer.Option("uncategorized", "--category", "-c", help="Expense category."),
) -> None:
    """Add a new expense."""
    if not description:
        raise typer.BadParameter("Description is required.")

    try:
        parsed_amount = normalize_amount(amount)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    normalized_category = category.strip().lower() or "uncategorized"
    normalized_description = " ".join(part.strip() for part in description).strip()
    if not normalized_description:
        raise typer.BadParameter("Description is required.")

    store = get_store()
    try:
        expense = store.add_expense(parsed_amount, normalized_description, normalized_category)
    finally:
        store.close()

    console.print(
        Panel.fit(
            f"Saved expense [bold]{money(expense.amount)}[/bold] for [cyan]{expense.description}[/cyan]\n"
            f"Category: [green]{expense.category}[/green]",
            title="Expense Added",
            border_style="green",
        )
    )


@app.command("list")
def list_expenses(
    limit: int = typer.Option(50, "--limit", "-n", min=1, help="Number of expenses to show."),
) -> None:
    """List saved expenses."""
    store = get_store()
    try:
        expenses = store.list_expenses(limit=limit)
    finally:
        store.close()

    if not expenses:
        console.print("No expenses saved yet. Run [bold]expense add 50 lunch[/bold].")
        return

    table = Table(title="Expenses")
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Date", style="cyan")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Description", overflow="fold")

    for expense in expenses:
        table.add_row(
            str(expense.id),
            expense.created_at.replace("T", " "),
            money(expense.amount),
            expense.category,
            expense.description,
        )

    console.print(table)


@app.command()
def report(
    month: str | None = typer.Option(
        None,
        "--month",
        "-m",
        help="Filter by month in YYYY-MM format.",
    ),
) -> None:
    """Show monthly totals and category breakdowns."""
    if month:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise typer.BadParameter("Month must use YYYY-MM format.") from exc

    store = get_store()
    try:
        monthly_rows = store.monthly_totals()
        category_rows = store.monthly_category_totals(month=month)
    finally:
        store.close()

    if not monthly_rows:
        console.print("No expenses saved yet. Add one before running reports.")
        return

    if not month:
        totals_table = Table(title="Monthly Totals")
        totals_table.add_column("Month", style="cyan")
        totals_table.add_column("Total", justify="right", style="green")
        totals_table.add_column("Chart", style="yellow")

        max_total = max(float(row["total"]) for row in monthly_rows) or 1.0
        for row in monthly_rows:
            total = float(row["total"])
            width = max(1, round((total / max_total) * 30))
            totals_table.add_row(row["month"], money(total), "█" * width)
        console.print(totals_table)

    grouped: dict[str, list[tuple[str, float]]] = {}
    for row in category_rows:
        grouped.setdefault(row["month"], []).append((row["category"], float(row["total"])))

    if month and month not in grouped:
        console.print(f"No expenses found for {month}.")
        raise typer.Exit(code=1)

    for group_month, items in grouped.items():
        category_table = Table(title=f"Category Breakdown · {group_month}")
        category_table.add_column("Category", style="magenta")
        category_table.add_column("Total", justify="right", style="green")
        category_table.add_column("Share", style="yellow")

        month_total = sum(total for _, total in items) or 1.0
        for category, total in items:
            width = max(1, round((total / month_total) * 30))
            category_table.add_row(category, money(total), "■" * width)

        console.print(category_table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

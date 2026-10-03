"""Calculations and text formatting for summaries and reports.

The calculation functions take a list of Transaction objects and return
numbers or dicts. The format_* functions turn those results into text that
main.py prints. Nothing in this file reads input or touches the disk.
"""

from datetime import datetime
from typing import Optional

from src.finance_manager import Transaction
from src.validators import DATE_FORMAT, MONTH_FORMAT

CURRENCY = "Rs."  # change this to "$", "EUR", etc. if you like


def money(amount: float) -> str:
    """Format a number like 'Rs. 1,250.50'."""
    return f"{CURRENCY} {amount:,.2f}"


# ---------- calculations ----------


def total_income(transactions: list) -> float:
    return round(sum(t.amount for t in transactions if t.type == "income"), 2)


def total_expenses(transactions: list) -> float:
    return round(sum(t.amount for t in transactions if t.type == "expense"), 2)


def balance(transactions: list) -> float:
    """Income minus expenses. Can be negative."""
    return round(total_income(transactions) - total_expenses(transactions), 2)


def total_savings(transactions: list) -> float:
    """Money left over. Never below zero (overspending is not 'negative savings')."""
    return max(balance(transactions), 0.0)


def spending_by_category(transactions: list) -> dict:
    """Return {category: total spent}, biggest category first."""
    totals = {}
    for transaction in transactions:
        if transaction.type == "expense":
            totals[transaction.category] = (
                totals.get(transaction.category, 0) + transaction.amount
            )
    rounded = {category: round(amount, 2) for category, amount in totals.items()}
    return dict(sorted(rounded.items(), key=lambda item: item[1], reverse=True))


def highest_spending_category(transactions: list) -> Optional[tuple]:
    """Return (category, amount) for the biggest expense category, or None."""
    totals = spending_by_category(transactions)
    if not totals:
        return None
    category = next(iter(totals))  # the dict is already sorted biggest-first
    return category, totals[category]


def transaction_month(transaction: Transaction) -> str:
    """Return the 'YYYY-MM' month a transaction belongs to."""
    parsed = datetime.strptime(transaction.date, DATE_FORMAT)
    return parsed.strftime(MONTH_FORMAT)


def filter_by_month(transactions: list, month: str) -> list:
    """Keep only the transactions that happened in the given 'YYYY-MM' month."""
    return [t for t in transactions if transaction_month(t) == month]


def financial_summary(transactions: list) -> dict:
    """All-time totals."""
    return {
        "total_income": total_income(transactions),
        "total_expenses": total_expenses(transactions),
        "balance": balance(transactions),
        "total_savings": total_savings(transactions),
        "highest_category": highest_spending_category(transactions),
    }


def monthly_summary(transactions: list, month: str) -> dict:
    """Totals and category-wise spending for one month."""
    month_transactions = filter_by_month(transactions, month)
    return {
        "month": month,
        "transaction_count": len(month_transactions),
        "total_income": total_income(month_transactions),
        "total_expenses": total_expenses(month_transactions),
        "balance": balance(month_transactions),
        "spending_by_category": spending_by_category(month_transactions),
    }


def budget_status(transactions: list, month: str, budget: Optional[float]) -> Optional[dict]:
    """Compare a month's spending with its budget. Returns None if no budget."""
    if budget is None:
        return None

    spent = total_expenses(filter_by_month(transactions, month))
    return {
        "month": month,
        "budget": budget,
        "spent": spent,
        "remaining": round(max(budget - spent, 0), 2),
        "exceeded_by": round(max(spent - budget, 0), 2),
        "percent_used": round(spent / budget * 100, 1),
    }


# ---------- text formatting ----------


def format_transactions_table(transactions: list) -> str:
    """Return the transactions as an aligned text table, oldest date first."""
    if not transactions:
        return "No transactions found."

    header = (
        f"{'ID':<4} {'Type':<8} {'Amount':>12}  {'Category/Source':<18} "
        f"{'Date':<10}  Note"
    )
    lines = [header, "-" * 75]
    for t in sorted(transactions, key=lambda item: (item.date, item.id)):
        lines.append(
            f"{t.id:<4} {t.type:<8} {t.amount:>12,.2f}  {t.category:<18} "
            f"{t.date:<10}  {t.note}"
        )
    return "\n".join(lines)


def format_financial_summary(summary: dict) -> str:
    lines = [
        "FINANCIAL SUMMARY",
        "-" * 40,
        f"Total income:     {money(summary['total_income'])}",
        f"Total expenses:   {money(summary['total_expenses'])}",
        f"Current balance:  {money(summary['balance'])}",
        f"Total savings:    {money(summary['total_savings'])}",
    ]
    highest = summary["highest_category"]
    if highest is None:
        lines.append("Top spending:     no expenses yet")
    else:
        lines.append(f"Top spending:     {highest[0]} ({money(highest[1])})")
    return "\n".join(lines)


def format_budget_status(status: dict) -> str:
    lines = [
        f"BUDGET FOR {status['month']}",
        "-" * 40,
        f"Monthly budget:   {money(status['budget'])}",
        f"Total spending:   {money(status['spent'])} ({status['percent_used']}% used)",
    ]
    if status["exceeded_by"] > 0:
        lines.append(f"OVER BUDGET by:   {money(status['exceeded_by'])}")
    else:
        lines.append(f"Remaining:        {money(status['remaining'])}")
    return "\n".join(lines)


def format_monthly_report(summary: dict, status: Optional[dict] = None) -> str:
    lines = [
        f"MONTHLY REPORT: {summary['month']}",
        "-" * 40,
        f"Transactions:     {summary['transaction_count']}",
        f"Total income:     {money(summary['total_income'])}",
        f"Total expenses:   {money(summary['total_expenses'])}",
        f"Balance:          {money(summary['balance'])}",
        "",
        "Spending by category:",
    ]
    if summary["spending_by_category"]:
        for category, amount in summary["spending_by_category"].items():
            lines.append(f"  {category:<15} {money(amount)}")
    else:
        lines.append("  No expenses this month.")

    if status is not None:
        lines.append("")
        lines.append(format_budget_status(status))
    return "\n".join(lines)

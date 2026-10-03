"""Personal Finance Tracker - terminal menu.

Run with:  python main.py

This file only handles talking to the user (menus and prompts). The real
work happens in the src/ modules.
"""

from datetime import date

from src import reports, validators
from src.finance_manager import FinanceManager

MENU = """
========================================
       PERSONAL FINANCE TRACKER
========================================

1. Add Income
2. Add Expense
3. View Transactions
4. Search / Filter
5. Financial Summary
6. Monthly Report
7. Set Monthly Budget
8. Edit Transaction
9. Delete Transaction
10. Exit
"""

CANCEL_HINT = "(Type 'cancel' at any prompt to go back to the menu.)"


class ActionCancelled(Exception):
    """Raised when the user types 'cancel' at a prompt."""


# ---------- prompt helpers ----------


def today_string() -> str:
    return date.today().strftime(validators.DATE_FORMAT)


def current_month_string() -> str:
    return date.today().strftime(validators.MONTH_FORMAT)


def ask(prompt: str, parser, default=None):
    """Keep asking until `parser` accepts the answer.

    If the user just presses Enter and a default exists, the default is used.
    """
    while True:
        raw = input(prompt).strip()
        if raw.lower() == "cancel":
            raise ActionCancelled
        if raw == "" and default is not None:
            raw = default
        try:
            return parser(raw)
        except ValueError as error:
            print(f"  Error: {error}")


def ask_optional(prompt: str, parser):
    """Like ask(), but pressing Enter returns None (meaning 'skip')."""
    while True:
        raw = input(prompt).strip()
        if raw.lower() == "cancel":
            raise ActionCancelled
        if raw == "":
            return None
        try:
            return parser(raw)
        except ValueError as error:
            print(f"  Error: {error}")


def ask_note(prompt: str = "Note (optional): ") -> str:
    raw = input(prompt).strip()
    if raw.lower() == "cancel":
        raise ActionCancelled
    return raw


def ask_existing_transaction(manager: FinanceManager, prompt: str):
    """Ask for an ID until it belongs to a real transaction."""
    while True:
        transaction_id = ask(prompt, validators.parse_transaction_id)
        try:
            return manager.get_transaction(transaction_id)
        except ValueError as error:
            print(f"  Error: {error}")


# ---------- menu actions ----------


def add_income_flow(manager: FinanceManager) -> None:
    print("\nADD INCOME")
    print(CANCEL_HINT)
    amount = ask("Amount: ", validators.parse_amount)
    source = ask("Source (e.g. Salary, Freelance): ", validators.validate_source)
    date_text = ask(
        f"Date YYYY-MM-DD [Enter = today, {today_string()}]: ",
        validators.parse_date,
        default=today_string(),
    )
    note = ask_note()

    transaction = manager.add_income(amount, source, date_text, note)
    print(f"\nIncome added (ID {transaction.id}): {reports.money(transaction.amount)} "
          f"from {transaction.category} on {transaction.date}.")


def add_expense_flow(manager: FinanceManager) -> None:
    print("\nADD EXPENSE")
    print(CANCEL_HINT)
    print("Categories: " + ", ".join(validators.EXPENSE_CATEGORIES))
    amount = ask("Amount: ", validators.parse_amount)
    category = ask("Category: ", validators.validate_category)
    date_text = ask(
        f"Date YYYY-MM-DD [Enter = today, {today_string()}]: ",
        validators.parse_date,
        default=today_string(),
    )
    note = ask_note()

    transaction = manager.add_expense(amount, category, date_text, note)
    print(f"\nExpense added (ID {transaction.id}): {reports.money(transaction.amount)} "
          f"on {transaction.category} on {transaction.date}.")


def view_transactions_flow(manager: FinanceManager) -> None:
    print("\nALL TRANSACTIONS")
    print(reports.format_transactions_table(manager.get_all()))


def search_flow(manager: FinanceManager) -> None:
    print("\nSEARCH / FILTER")
    print("Fill in any filters you want. Press Enter to skip one.")
    print(CANCEL_HINT)
    transaction_type = ask_optional(
        "Type (income/expense): ", validators.validate_transaction_type
    )
    category = ask_optional("Category or source: ", validators.validate_source)
    date_text = ask_optional("Date (YYYY-MM-DD): ", validators.parse_date)
    transaction_id = ask_optional("Transaction ID: ", validators.parse_transaction_id)

    results = manager.filter_transactions(
        transaction_type, category, date_text, transaction_id
    )
    print(f"\nFound {len(results)} transaction(s).")
    print(reports.format_transactions_table(results))


def financial_summary_flow(manager: FinanceManager) -> None:
    print()
    summary = reports.financial_summary(manager.get_all())
    print(reports.format_financial_summary(summary))


def monthly_report_flow(manager: FinanceManager) -> None:
    print("\nMONTHLY REPORT")
    print(CANCEL_HINT)
    month = ask(
        f"Month YYYY-MM [Enter = this month, {current_month_string()}]: ",
        validators.parse_month,
        default=current_month_string(),
    )
    transactions = manager.get_all()
    summary = reports.monthly_summary(transactions, month)
    status = reports.budget_status(transactions, month, manager.get_budget(month))

    print()
    print(reports.format_monthly_report(summary, status))
    if status is None:
        print("\n(No budget set for this month. Use option 7 to set one.)")


def set_budget_flow(manager: FinanceManager) -> None:
    print("\nMONTHLY BUDGET")
    print(CANCEL_HINT)
    month = ask(
        f"Month YYYY-MM [Enter = this month, {current_month_string()}]: ",
        validators.parse_month,
        default=current_month_string(),
    )

    current_budget = manager.get_budget(month)
    if current_budget is None:
        print(f"No budget is set for {month} yet.")
        new_budget = ask("Budget amount: ", validators.parse_amount)
    else:
        print(f"Current budget for {month}: {reports.money(current_budget)}")
        new_budget = ask_optional(
            "New budget amount (Enter to keep it): ", validators.parse_amount
        )

    if new_budget is not None:
        manager.set_budget(month, new_budget)
        print(f"Budget for {month} set to {reports.money(new_budget)}.")

    status = reports.budget_status(manager.get_all(), month, manager.get_budget(month))
    print()
    print(reports.format_budget_status(status))


def edit_transaction_flow(manager: FinanceManager) -> None:
    print("\nEDIT TRANSACTION")
    print(CANCEL_HINT)
    transaction = ask_existing_transaction(manager, "Transaction ID to edit: ")

    print("\nCurrent details:")
    print(reports.format_transactions_table([transaction]))
    print("\nPress Enter to keep a value as it is.")

    amount = ask_optional(
        f"New amount [{transaction.amount:,.2f}]: ", validators.parse_amount
    )

    if transaction.type == "expense":
        print("Categories: " + ", ".join(validators.EXPENSE_CATEGORIES))
        category_parser = validators.validate_category
    else:
        category_parser = validators.validate_source
    category = ask_optional(f"New category/source [{transaction.category}]: ", category_parser)

    date_text = ask_optional(f"New date [{transaction.date}]: ", validators.parse_date)

    note_raw = input("New note (Enter = keep, '-' = clear): ").strip()
    if note_raw.lower() == "cancel":
        raise ActionCancelled
    if note_raw == "":
        note = None  # None means "leave unchanged"
    elif note_raw == "-":
        note = ""
    else:
        note = note_raw

    updated = manager.edit_transaction(transaction.id, amount, category, date_text, note)
    print("\nTransaction updated:")
    print(reports.format_transactions_table([updated]))


def delete_transaction_flow(manager: FinanceManager) -> None:
    print("\nDELETE TRANSACTION")
    print(CANCEL_HINT)
    transaction = ask_existing_transaction(manager, "Transaction ID to delete: ")

    print()
    print(reports.format_transactions_table([transaction]))
    answer = input("\nAre you sure you want to delete this? (yes/no): ").strip().lower()
    if answer in ("y", "yes"):
        manager.delete_transaction(transaction.id)
        print(f"Transaction {transaction.id} deleted.")
    else:
        print("Deletion cancelled. Nothing was changed.")


# ---------- main loop ----------


def main() -> None:
    try:
        manager = FinanceManager()
    except OSError as error:
        print(f"Could not open the data file: {error}")
        return

    actions = {
        "1": add_income_flow,
        "2": add_expense_flow,
        "3": view_transactions_flow,
        "4": search_flow,
        "5": financial_summary_flow,
        "6": monthly_report_flow,
        "7": set_budget_flow,
        "8": edit_transaction_flow,
        "9": delete_transaction_flow,
    }

    while True:
        print(MENU)
        try:
            choice = input("Choose an option: ").strip()
            if choice == "10":
                print("Goodbye! Your data is saved.")
                break

            action = actions.get(choice)
            if action is None:
                print("Invalid choice. Please enter a number from 1 to 10.")
                continue
            action(manager)
        except ActionCancelled:
            print("Cancelled. Back to the menu.")
        except OSError as error:
            print(f"Could not save your data: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()

"""Input validation helpers.

Every function here takes the text a user typed, checks it, and either
returns a clean value or raises ValueError with a message that is safe to
show directly to the user.
"""

import math
from datetime import datetime

EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Education",
    "Entertainment",
    "Bills",
    "Health",
    "Other",
]

TRANSACTION_TYPES = ("income", "expense")

DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"


def parse_amount(text) -> float:
    """Turn user input into a positive amount rounded to 2 decimals."""
    cleaned = str(text).strip().replace(",", "")
    if not cleaned:
        raise ValueError("Amount cannot be empty.")

    try:
        amount = float(cleaned)
    except ValueError:
        raise ValueError(f"'{cleaned}' is not a valid number.") from None

    if math.isnan(amount) or math.isinf(amount):
        raise ValueError("Amount must be a real number.")

    amount = round(amount, 2)
    if amount < 0:
        raise ValueError("Amount cannot be negative.")
    if amount == 0:
        raise ValueError("Amount must be greater than zero.")
    return amount


def parse_date(text) -> str:
    """Check a date typed as YYYY-MM-DD and return it in that same format."""
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("Date cannot be empty.")

    try:
        parsed = datetime.strptime(cleaned, DATE_FORMAT)
    except ValueError:
        raise ValueError(
            f"'{cleaned}' is not a valid date. Use YYYY-MM-DD, e.g. 2026-10-03."
        ) from None
    return parsed.strftime(DATE_FORMAT)


def parse_month(text) -> str:
    """Check a month typed as YYYY-MM and return it in that same format."""
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("Month cannot be empty.")

    try:
        parsed = datetime.strptime(cleaned, MONTH_FORMAT)
    except ValueError:
        raise ValueError(
            f"'{cleaned}' is not a valid month. Use YYYY-MM, e.g. 2026-10."
        ) from None
    return parsed.strftime(MONTH_FORMAT)


def validate_category(text) -> str:
    """Match an expense category (ignoring upper/lower case) to the official list."""
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("Category cannot be empty.")

    for category in EXPENSE_CATEGORIES:
        if category.lower() == cleaned.lower():
            return category
    raise ValueError(
        f"'{cleaned}' is not a valid category. Choose from: "
        + ", ".join(EXPENSE_CATEGORIES)
        + "."
    )


def validate_source(text) -> str:
    """Income sources are free text, but they cannot be empty."""
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("Source cannot be empty.")
    return cleaned


def validate_transaction_type(text) -> str:
    """Accept only 'income' or 'expense' (any capitalisation)."""
    cleaned = str(text).strip().lower()
    if cleaned not in TRANSACTION_TYPES:
        raise ValueError("Type must be 'income' or 'expense'.")
    return cleaned


def parse_transaction_id(text) -> int:
    """Turn user input into a positive whole-number transaction ID."""
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("Transaction ID cannot be empty.")

    try:
        transaction_id = int(cleaned)
    except ValueError:
        raise ValueError(f"'{cleaned}' is not a valid transaction ID.") from None

    if transaction_id <= 0:
        raise ValueError("Transaction ID must be a positive number.")
    return transaction_id

"""Reading and writing the JSON data file.

This module knows how to load and save plain Python data (dicts and lists).
It knows nothing about menus or reports.

The file looks like this:

    {
      "transactions": [ {"id": 1, "type": "income", ...}, ... ],
      "budgets": {"2026-10": 15000.0}
    }
"""

import json
import os
from datetime import datetime
from pathlib import Path

from src import validators

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "transactions.json"


def empty_data() -> dict:
    """Return the structure used when there is nothing saved yet."""
    return {"transactions": [], "budgets": {}}


def save_data(data: dict, path: Path = DEFAULT_DATA_FILE) -> None:
    """Write data to the JSON file.

    We write to a temporary file first and then swap it in, so a crash in the
    middle of saving can never leave a half-written data file behind.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)


def load_data(path: Path = DEFAULT_DATA_FILE) -> dict:
    """Load saved data, creating the file if it is missing.

    If the file is corrupted, it is renamed (not deleted) and a fresh empty
    file is created, so the program can keep running.
    """
    path = Path(path)

    if not path.exists():
        data = empty_data()
        save_data(data, path)
        return data

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _recover_from_corrupted_file(path)

    if not _is_valid_data(data):
        return _recover_from_corrupted_file(path)
    return data


def _recover_from_corrupted_file(path: Path) -> dict:
    """Move the bad file aside, start fresh, and tell the user."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.stem}.corrupted-{timestamp}{path.suffix}")
    os.replace(path, backup_path)

    data = empty_data()
    save_data(data, path)
    print(f"Warning: {path.name} was damaged or unreadable.")
    print(f"  The old file was kept as {backup_path.name}.")
    print("  Starting with an empty transaction list.")
    return data


def _is_valid_data(data) -> bool:
    """Check that loaded JSON has the structure the program expects."""
    if not isinstance(data, dict):
        return False

    transactions = data.get("transactions")
    if not isinstance(transactions, list):
        return False

    seen_ids = set()
    for record in transactions:
        if not _is_valid_record(record) or record["id"] in seen_ids:
            return False
        seen_ids.add(record["id"])

    budgets = data.setdefault("budgets", {})
    if not isinstance(budgets, dict):
        return False
    try:
        for month, amount in budgets.items():
            validators.parse_month(month)
            validators.parse_amount(amount)
    except (ValueError, TypeError):
        return False
    return True


def _is_valid_record(record) -> bool:
    """Check one saved transaction has all fields with sensible values."""
    if not isinstance(record, dict):
        return False

    try:
        validators.parse_transaction_id(record["id"])
        validators.parse_amount(record["amount"])
        validators.parse_date(record["date"])
        category = record["category"]
        note = record.get("note", "")
        return (
            record["type"] in validators.TRANSACTION_TYPES
            and isinstance(record["id"], int)
            and isinstance(category, str)
            and category.strip() != ""
            and isinstance(note, str)
        )
    except (KeyError, ValueError, TypeError):
        return False

"""The core of the app: the Transaction record and the FinanceManager.

FinanceManager owns the list of transactions and the budgets. Every change
(add, edit, delete, set budget) is validated first and then saved to disk
straight away.
"""

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from src import storage, validators


@dataclass
class Transaction:
    """One income or expense record.

    For income, `category` holds the source (e.g. "Salary").
    """

    id: int
    type: str  # "income" or "expense"
    amount: float
    category: str
    date: str  # always "YYYY-MM-DD"
    note: str = ""

    def to_dict(self) -> dict:
        """Convert to a plain dict so it can be written as JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Build a Transaction from a dict loaded from JSON."""
        return cls(
            id=int(data["id"]),
            type=data["type"],
            amount=float(data["amount"]),
            category=data["category"],
            date=data["date"],
            note=data.get("note", ""),
        )


class FinanceManager:
    """Keeps all transactions and budgets in memory and in the JSON file."""

    def __init__(self, data_file: Path = storage.DEFAULT_DATA_FILE) -> None:
        self.data_file = Path(data_file)
        data = storage.load_data(self.data_file)
        self.transactions = [Transaction.from_dict(r) for r in data["transactions"]]
        self.budgets = dict(data["budgets"])

    # ---------- saving ----------

    def _save(self) -> None:
        data = {
            "transactions": [t.to_dict() for t in self.transactions],
            "budgets": self.budgets,
        }
        storage.save_data(data, self.data_file)

    def _next_id(self) -> int:
        if not self.transactions:
            return 1
        return max(t.id for t in self.transactions) + 1

    # ---------- adding ----------

    def add_income(
        self, amount, source, date_text: Optional[str] = None, note: str = ""
    ) -> Transaction:
        """Validate and add an income transaction."""
        source = validators.validate_source(source)
        return self._add_transaction("income", amount, source, date_text, note)

    def add_expense(
        self, amount, category, date_text: Optional[str] = None, note: str = ""
    ) -> Transaction:
        """Validate and add an expense transaction."""
        category = validators.validate_category(category)
        return self._add_transaction("expense", amount, category, date_text, note)

    def _add_transaction(
        self,
        transaction_type: str,
        amount,
        category: str,
        date_text: Optional[str],
        note: str,
    ) -> Transaction:
        # Validate everything BEFORE changing any data.
        clean_amount = validators.parse_amount(amount)
        if date_text is None:
            clean_date = date.today().strftime(validators.DATE_FORMAT)
        else:
            clean_date = validators.parse_date(date_text)

        transaction = Transaction(
            id=self._next_id(),
            type=transaction_type,
            amount=clean_amount,
            category=category,
            date=clean_date,
            note=(note or "").strip(),
        )
        self.transactions.append(transaction)
        self._save()
        return transaction

    # ---------- reading ----------

    def get_all(self) -> list:
        """Return a copy of the transaction list."""
        return list(self.transactions)

    def get_transaction(self, transaction_id: int) -> Transaction:
        """Find a transaction by ID or raise ValueError."""
        for transaction in self.transactions:
            if transaction.id == transaction_id:
                return transaction
        raise ValueError(f"No transaction found with ID {transaction_id}.")

    def filter_transactions(
        self,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        date_text: Optional[str] = None,
        transaction_id: Optional[int] = None,
    ) -> list:
        """Return transactions matching ALL the filters that were given.

        A filter left as None is ignored.
        """
        results = []
        for transaction in self.transactions:
            if transaction_type and transaction.type != transaction_type.lower():
                continue
            if category and transaction.category.lower() != category.strip().lower():
                continue
            if date_text and transaction.date != date_text:
                continue
            if transaction_id is not None and transaction.id != transaction_id:
                continue
            results.append(transaction)
        return results

    # ---------- editing and deleting ----------

    def edit_transaction(
        self,
        transaction_id: int,
        amount=None,
        category=None,
        date_text=None,
        note=None,
    ) -> Transaction:
        """Change the fields that are not None. The type cannot be changed."""
        transaction = self.get_transaction(transaction_id)

        # Validate everything first, then apply, so a bad value changes nothing.
        new_amount = transaction.amount
        new_category = transaction.category
        new_date = transaction.date
        new_note = transaction.note

        if amount is not None:
            new_amount = validators.parse_amount(amount)
        if category is not None:
            if transaction.type == "expense":
                new_category = validators.validate_category(category)
            else:
                new_category = validators.validate_source(category)
        if date_text is not None:
            new_date = validators.parse_date(date_text)
        if note is not None:
            new_note = note.strip()

        transaction.amount = new_amount
        transaction.category = new_category
        transaction.date = new_date
        transaction.note = new_note
        self._save()
        return transaction

    def delete_transaction(self, transaction_id: int) -> Transaction:
        """Remove a transaction and return it."""
        transaction = self.get_transaction(transaction_id)
        self.transactions.remove(transaction)
        self._save()
        return transaction

    # ---------- budgets ----------

    def set_budget(self, month: str, amount) -> float:
        """Set the budget for a month (format YYYY-MM)."""
        clean_month = validators.parse_month(month)
        clean_amount = validators.parse_amount(amount)
        self.budgets[clean_month] = clean_amount
        self._save()
        return clean_amount

    def get_budget(self, month: str) -> Optional[float]:
        """Return the budget for a month, or None if none was set."""
        return self.budgets.get(validators.parse_month(month))

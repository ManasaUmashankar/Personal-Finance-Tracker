"""Tests for the Personal Finance Tracker.

Run from the project folder with:
    python -m unittest discover -s tests -v
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

# Lets this file also run directly (python tests/test_finance.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import reports, storage, validators  # noqa: E402
from src.finance_manager import FinanceManager  # noqa: E402


class FinanceTestCase(unittest.TestCase):
    """Base class: every test gets a fresh manager using a temporary file."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "transactions.json"
        self.manager = FinanceManager(self.data_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_sample_data(self):
        self.manager.add_income(50000, "Salary", "2026-10-01")
        self.manager.add_income(2000, "Freelance", "2026-10-15")
        self.manager.add_expense(1200, "Food", "2026-10-02")
        self.manager.add_expense(800, "Food", "2026-10-10")
        self.manager.add_expense(500, "Transport", "2026-10-11")
        self.manager.add_expense(3000, "Bills", "2026-09-28")  # previous month


class TestAddingTransactions(FinanceTestCase):
    def test_add_income(self):
        transaction = self.manager.add_income(1000, "Salary", "2026-10-01", "Oct pay")
        self.assertEqual(transaction.id, 1)
        self.assertEqual(transaction.type, "income")
        self.assertEqual(transaction.amount, 1000.0)
        self.assertEqual(transaction.category, "Salary")
        self.assertEqual(transaction.note, "Oct pay")
        self.assertEqual(len(self.manager.get_all()), 1)

    def test_add_expense_fixes_category_capitalisation(self):
        transaction = self.manager.add_expense("250.50", "food", "2026-10-02")
        self.assertEqual(transaction.category, "Food")
        self.assertEqual(transaction.amount, 250.5)

    def test_ids_increase(self):
        first = self.manager.add_income(10, "A", "2026-10-01")
        second = self.manager.add_expense(5, "Food", "2026-10-01")
        self.assertEqual((first.id, second.id), (1, 2))

    def test_date_defaults_to_today(self):
        transaction = self.manager.add_income(10, "Gift")
        validators.parse_date(transaction.date)  # must be a valid date


class TestCalculations(FinanceTestCase):
    def test_totals_and_balance(self):
        self.add_sample_data()
        transactions = self.manager.get_all()
        self.assertEqual(reports.total_income(transactions), 52000.0)
        self.assertEqual(reports.total_expenses(transactions), 5500.0)
        self.assertEqual(reports.balance(transactions), 46500.0)
        self.assertEqual(reports.total_savings(transactions), 46500.0)

    def test_empty_data(self):
        transactions = self.manager.get_all()
        self.assertEqual(reports.balance(transactions), 0)
        self.assertIsNone(reports.highest_spending_category(transactions))

    def test_savings_never_negative(self):
        self.manager.add_income(100, "Gift", "2026-10-01")
        self.manager.add_expense(300, "Shopping", "2026-10-02")
        transactions = self.manager.get_all()
        self.assertEqual(reports.balance(transactions), -200.0)
        self.assertEqual(reports.total_savings(transactions), 0.0)

    def test_decimal_amounts_add_up(self):
        self.manager.add_expense(0.1, "Food", "2026-10-01")
        self.manager.add_expense(0.2, "Food", "2026-10-01")
        self.assertEqual(reports.total_expenses(self.manager.get_all()), 0.3)

    def test_highest_spending_category(self):
        self.add_sample_data()
        # Bills (3000) beats Food (2000) over all time
        self.assertEqual(
            reports.highest_spending_category(self.manager.get_all()),
            ("Bills", 3000.0),
        )

    def test_monthly_summary_only_counts_that_month(self):
        self.add_sample_data()
        summary = reports.monthly_summary(self.manager.get_all(), "2026-10")
        self.assertEqual(summary["total_income"], 52000.0)
        self.assertEqual(summary["total_expenses"], 2500.0)
        self.assertEqual(summary["balance"], 49500.0)
        self.assertEqual(
            summary["spending_by_category"], {"Food": 2000.0, "Transport": 500.0}
        )

    def test_monthly_summary_empty_month(self):
        self.add_sample_data()
        summary = reports.monthly_summary(self.manager.get_all(), "2025-01")
        self.assertEqual(summary["transaction_count"], 0)
        self.assertEqual(summary["spending_by_category"], {})


class TestBudget(FinanceTestCase):
    def test_budget_remaining(self):
        self.add_sample_data()
        self.manager.set_budget("2026-10", 4000)
        status = reports.budget_status(
            self.manager.get_all(), "2026-10", self.manager.get_budget("2026-10")
        )
        self.assertEqual(status["spent"], 2500.0)
        self.assertEqual(status["remaining"], 1500.0)
        self.assertEqual(status["exceeded_by"], 0)

    def test_budget_exceeded(self):
        self.add_sample_data()
        self.manager.set_budget("2026-10", 2000)
        status = reports.budget_status(
            self.manager.get_all(), "2026-10", self.manager.get_budget("2026-10")
        )
        self.assertEqual(status["remaining"], 0)
        self.assertEqual(status["exceeded_by"], 500.0)

    def test_no_budget_returns_none(self):
        self.assertIsNone(self.manager.get_budget("2026-10"))
        self.assertIsNone(reports.budget_status([], "2026-10", None))

    def test_invalid_budget_inputs(self):
        with self.assertRaises(ValueError):
            self.manager.set_budget("2026-13", 1000)
        with self.assertRaises(ValueError):
            self.manager.set_budget("2026-10", -5)
        with self.assertRaises(ValueError):
            self.manager.set_budget("2026-10", 0)


class TestInvalidInput(FinanceTestCase):
    def test_bad_amounts(self):
        for bad in ["-5", "0", "0.001", "", "   ", "abc", "nan", "inf", "5x"]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.manager.add_income(bad, "Salary", "2026-10-01")
        self.assertEqual(self.manager.get_all(), [])  # nothing was saved

    def test_bad_dates(self):
        for bad in ["2026-02-30", "10/03/2026", "yesterday", "", "2026-13-01"]:
            with self.subTest(date=bad):
                with self.assertRaises(ValueError):
                    self.manager.add_expense(10, "Food", bad)

    def test_bad_category_and_source(self):
        with self.assertRaises(ValueError):
            self.manager.add_expense(10, "Pizza", "2026-10-01")
        with self.assertRaises(ValueError):
            self.manager.add_expense(10, "", "2026-10-01")
        with self.assertRaises(ValueError):
            self.manager.add_income(10, "   ", "2026-10-01")

    def test_bad_transaction_ids(self):
        for bad in ["", "abc", "-1", "0", "1.5"]:
            with self.subTest(id=bad):
                with self.assertRaises(ValueError):
                    validators.parse_transaction_id(bad)

    def test_validators_clean_good_input(self):
        self.assertEqual(validators.parse_amount(" 1,250.456 "), 1250.46)
        self.assertEqual(validators.parse_date("2026-1-5"), "2026-01-05")
        self.assertEqual(validators.parse_month("2026-10"), "2026-10")
        self.assertEqual(validators.validate_transaction_type("INCOME"), "income")


class TestEditDeleteFilter(FinanceTestCase):
    def test_edit_changes_only_given_fields(self):
        original = self.manager.add_expense(100, "Food", "2026-10-01", "lunch")
        self.manager.edit_transaction(original.id, amount=150, category="Bills")
        edited = self.manager.get_transaction(original.id)
        self.assertEqual(edited.amount, 150.0)
        self.assertEqual(edited.category, "Bills")
        self.assertEqual(edited.date, "2026-10-01")
        self.assertEqual(edited.note, "lunch")

    def test_edit_can_clear_note(self):
        original = self.manager.add_income(100, "Gift", "2026-10-01", "old note")
        self.manager.edit_transaction(original.id, note="")
        self.assertEqual(self.manager.get_transaction(original.id).note, "")

    def test_bad_edit_changes_nothing(self):
        original = self.manager.add_expense(100, "Food", "2026-10-01")
        with self.assertRaises(ValueError):
            self.manager.edit_transaction(original.id, amount=200, date_text="nope")
        self.assertEqual(self.manager.get_transaction(original.id).amount, 100.0)

    def test_edit_missing_id(self):
        with self.assertRaises(ValueError):
            self.manager.edit_transaction(99, amount=5)

    def test_delete(self):
        first = self.manager.add_income(100, "A", "2026-10-01")
        second = self.manager.add_income(200, "B", "2026-10-01")
        self.manager.delete_transaction(first.id)
        remaining = self.manager.get_all()
        self.assertEqual([t.id for t in remaining], [second.id])

    def test_delete_missing_id(self):
        with self.assertRaises(ValueError):
            self.manager.delete_transaction(42)

    def test_filters(self):
        self.add_sample_data()
        manager = self.manager
        self.assertEqual(len(manager.filter_transactions(transaction_type="income")), 2)
        self.assertEqual(len(manager.filter_transactions(transaction_type="expense")), 4)
        self.assertEqual(len(manager.filter_transactions(category="food")), 2)
        self.assertEqual(len(manager.filter_transactions(date_text="2026-10-10")), 1)
        self.assertEqual(len(manager.filter_transactions(transaction_id=1)), 1)
        self.assertEqual(
            len(manager.filter_transactions(transaction_type="expense", category="Food")), 2
        )
        self.assertEqual(len(manager.filter_transactions(category="Nothing")), 0)
        self.assertEqual(len(manager.filter_transactions()), 6)  # no filters = all


class TestStorage(FinanceTestCase):
    def test_file_is_created_if_missing(self):
        self.assertTrue(self.data_file.exists())

    def test_data_persists_between_runs(self):
        self.add_sample_data()
        self.manager.set_budget("2026-10", 4000)
        reloaded = FinanceManager(self.data_file)
        self.assertEqual(len(reloaded.get_all()), 6)
        self.assertEqual(reloaded.get_budget("2026-10"), 4000.0)

    def test_new_id_after_reload_does_not_clash(self):
        self.add_sample_data()
        reloaded = FinanceManager(self.data_file)
        new = reloaded.add_income(1, "Gift", "2026-10-20")
        self.assertEqual(new.id, 7)

    def test_corrupted_json_is_handled(self):
        self.data_file.write_text("{ this is not json", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            manager = FinanceManager(self.data_file)
        self.assertEqual(manager.get_all(), [])
        self.assertIn("damaged", output.getvalue())
        backups = list(Path(self.temp_dir.name).glob("transactions.corrupted-*.json"))
        self.assertEqual(len(backups), 1)
        manager.add_income(10, "Gift", "2026-10-01")  # still works afterwards
        self.assertEqual(len(FinanceManager(self.data_file).get_all()), 1)

    def test_wrong_structure_is_treated_as_corrupted(self):
        self.data_file.write_text('{"transactions": "oops"}', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            manager = FinanceManager(self.data_file)
        self.assertEqual(manager.get_all(), [])

    def test_bad_record_is_treated_as_corrupted(self):
        bad = {"transactions": [{"id": 1, "type": "income", "amount": -5,
                                 "category": "X", "date": "2026-10-01"}]}
        storage.save_data(bad, self.data_file)
        with contextlib.redirect_stdout(io.StringIO()):
            manager = FinanceManager(self.data_file)
        self.assertEqual(manager.get_all(), [])

    def test_empty_file_is_treated_as_corrupted(self):
        self.data_file.write_text("", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            manager = FinanceManager(self.data_file)
        self.assertEqual(manager.get_all(), [])


class TestFormatting(FinanceTestCase):
    def test_table_and_empty_table(self):
        self.assertEqual(reports.format_transactions_table([]), "No transactions found.")
        self.add_sample_data()
        table = reports.format_transactions_table(self.manager.get_all())
        self.assertIn("Salary", table)
        self.assertIn("2026-10-01", table)

    def test_monthly_report_text(self):
        self.add_sample_data()
        self.manager.set_budget("2026-10", 2000)
        transactions = self.manager.get_all()
        summary = reports.monthly_summary(transactions, "2026-10")
        status = reports.budget_status(transactions, "2026-10", 2000)
        text = reports.format_monthly_report(summary, status)
        self.assertIn("OVER BUDGET", text)
        self.assertIn("Food", text)


if __name__ == "__main__":
    unittest.main()

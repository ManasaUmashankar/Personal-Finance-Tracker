# Personal Finance Tracker

A command-line app for tracking your income, expenses and monthly budget. It's written in plain Python with no external libraries, and all your data is stored in a single JSON file on your own computer.

I built this project as a way to practise core Python skills (functions, modules, file handling, JSON, exception handling, `datetime` and a little OOP) on something that's actually useful, rather than another throwaway exercise.

## Features

- Add income (amount, source, date, optional note)
- Add expenses (amount, category, date, optional note)
- View all transactions in a table
- Search/filter by type, category, date or transaction ID (filters can be combined)
- Financial summary: total income, total expenses, balance, savings and your biggest spending category
- Monthly report with category-wise spending
- Monthly budget: see what you've spent, what's left, or how far over budget you are
- Edit and delete transactions (deleting always asks for confirmation)
- Data is saved automatically after every change
- Bad input never crashes the app: you get a clear message and another try. Type `cancel` at any prompt to go back to the menu.

## Technologies used

- Python 3.8 or newer
- Standard library only: `json`, `datetime`, `pathlib`, `dataclasses`, `unittest`

## Project structure

```text
Personal-Finance-Tracker/
├── main.py                  # Menu and prompts (the part you interact with)
├── README.md
├── requirements.txt         # Empty on purpose: no packages needed
├── .gitignore
├── data/
│   └── transactions.json    # Your data (created automatically)
├── src/
│   ├── __init__.py
│   ├── validators.py        # Checks and cleans what the user types
│   ├── storage.py           # Reads and writes the JSON file
│   ├── finance_manager.py   # Transaction class + FinanceManager class
│   └── reports.py           # Totals, summaries and text formatting
└── tests/
    └── test_finance.py      # 36 unit tests
```

## How it works

1. `main.py` shows the menu and asks questions.
2. Every answer goes through a function in `validators.py`. If it's invalid, the user sees the error and is asked again.
3. Valid data is passed to `FinanceManager`, which adds, edits or deletes transactions and saves immediately through `storage.py`.
4. For summaries, `reports.py` does the maths on the list of transactions and formats the result as text, which `main.py` prints.

## Installation

You only need Python installed. Check with:

```bash
python --version
```

(On some systems the command is `python3`.) Then download or clone this folder. There is nothing to `pip install`.

## How to run

From inside the project folder:

```bash
python main.py
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Example usage

```text
Choose an option: 1

ADD INCOME
(Type 'cancel' at any prompt to go back to the menu.)
Amount: -500
  Error: Amount cannot be negative.
Amount: 50000
Source (e.g. Salary, Freelance): Salary
Date YYYY-MM-DD [Enter = today, 2026-10-03]: 2026-10-01
Note (optional): October pay

Income added (ID 1): Rs. 50,000.00 from Salary on 2026-10-01.

Choose an option: 6

MONTHLY REPORT
Month YYYY-MM [Enter = this month, 2026-10]:

MONTHLY REPORT: 2026-10
----------------------------------------
Transactions:     3
Total income:     Rs. 50,000.00
Total expenses:   Rs. 2,000.00
Balance:          Rs. 48,000.00

Spending by category:
  Food            Rs. 1,200.00
  Transport       Rs. 800.00

BUDGET FOR 2026-10
----------------------------------------
Monthly budget:   Rs. 1,500.00
Total spending:   Rs. 2,000.00 (133.3% used)
OVER BUDGET by:   Rs. 500.00
```

The currency label is a single constant (`CURRENCY` in `src/reports.py`). Change it to `$`, `EUR` or whatever you use.

## Python concepts practised

| Concept | Where to look |
| --- | --- |
| Functions, parameters, return values, default arguments | Everywhere, e.g. `ask()` in `main.py` |
| Modules | The four files in `src/`, imported with `from src import ...` |
| File handling | `load_data()` / `save_data()` in `storage.py` |
| JSON | `json.load` and `json.dump` in `storage.py` |
| Exception handling | `try/except` in `validators.py`, `storage.py` and the main loop |
| `datetime` | Date/month validation and monthly filtering |
| OOP | `Transaction` (a dataclass) and `FinanceManager` |
| Lists, dicts, loops, f-strings | `reports.py` |
| Testing | `unittest` in `tests/test_finance.py` |

## Future improvements

Ideas to try yourself, roughly easiest first:

- Add a "date range" option to Search/Filter
- Export transactions to a CSV file with the `csv` module
- Let each category have its own monthly budget
- Add recurring transactions (e.g. rent on the 1st)
- Switch money amounts from `float` to `decimal.Decimal`
- Show a simple text bar chart of spending by category
- Add more tests for `main.py` (try `unittest.mock.patch("builtins.input")`)

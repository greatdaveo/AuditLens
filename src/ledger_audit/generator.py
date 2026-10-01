from datetime import datetime, timedelta
import random
import pandas as pd
from ledger_audit.chart_of_accounts import accounts_of_type
import calendar


USERS = ["U01", "U02", "U03", "U04", "U05", "U06", "U07", "U08"]
APPROVERS = ["A01", "A02", "A03"]
VAT_RATE = 0.20
WORKING_HOUR_START = 9
WORKING_HOUR_END = 18
USER_ROLES: dict[str, str] = {
    "U01": "sales",
    "U02": "purchasing",
    "U03": "sales",
    "U04": "purchasing",
    "U05": "sales",
    "U06": "purchasing",
    "U07": "sales",
    "U08": "payroll",

}
SALARY_PENCE: dict[str, int] = {
    "U01": 350000,
    "U02": 250000,
    "U03": 450000,
    "U04": 550000,
    "U05": 500000,
    "U06": 400000,
    "U07": 300000,
    "U08": 600000,
}


def generate_ledger(n_entries: int, seed: int, start: datetime, days: int) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    columns = ["entry_id", "line_no", "posted_at", "account_code",
               "debit_pence", "credit_pence", "user_id", "approver_id", "description"]
    expense_accounts = accounts_of_type("expense")

    last_random_date = start + timedelta(days=days - 1)
    month_cursor = datetime(start.year, start.month, 1)
    final_month = datetime(last_random_date.year, last_random_date.month, 1)
    payroll_dates = []

    while month_cursor <= final_month:
        final_day_number = calendar.monthrange(
            month_cursor.year, month_cursor.month)[1]
        payroll_date = datetime(
            month_cursor.year, month_cursor.month, final_day_number)

        while payroll_date.weekday() >= 5:
            payroll_date -= timedelta(days=1)

        if payroll_date.date() >= start.date():
            payroll_dates.append(payroll_date)

        if month_cursor.month == 12:
            month_cursor = datetime(month_cursor.year + 1, 1, 1)
        else:
            month_cursor = datetime(
                month_cursor.year, month_cursor.month + 1, 1)

    vat_settlement_dates = [
        date for date in payroll_dates if date.month in (3, 6, 9, 12)
    ]
    scheduled_count = len(payroll_dates) * len(USERS) + \
        len(vat_settlement_dates)

    if n_entries < scheduled_count:
        raise ValueError(
            "n_entries must be at least the number of scheduled entries")

    ordinary_count = n_entries - scheduled_count

    quarterly_vat: dict[tuple[int, int], int] = {}

    for entry_id in range(1, ordinary_count + 1):
        while True:
            posted_at = start + timedelta(days=rng.randrange(days))
            if posted_at.weekday() < 5:
                break
        posted_at = posted_at.replace(
            hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
            minute=rng.randrange(60),
            second=0,
            microsecond=0,
        )

        user_id = rng.choice(USERS)
        approver_id = rng.choice(APPROVERS)
        assert approver_id != user_id

        amount_pence = max(100, int(rng.lognormvariate(6.0, 1.0) * 100))
        event_type = rng.choice([
            "sale",
            "expense",
            "supplier_payment",
            "customer_receipt",
        ])

        if event_type == "sale":
            description = "Sale"
            legs = [
                (1100, amount_pence, 0),
                (4000, 0, amount_pence)
            ]
        elif event_type == "expense":
            description = "Expense"
            expense_account = rng.choice(expense_accounts)
            vat_pence = round(amount_pence * VAT_RATE)
            quarter = (posted_at.year, (posted_at.month - 1) // 3 + 1)
            quarterly_vat[quarter] = quarterly_vat.get(quarter, 0) + vat_pence
            legs = [
                (expense_account.code, amount_pence, 0),
                (1200, vat_pence, 0),
                (2000, 0, amount_pence + vat_pence),
            ]
        elif event_type == "supplier_payment":
            description = "Supplier payment"
            legs = [
                (2000, amount_pence, 0),
                (1000, 0, amount_pence),
            ]
        else:
            description = "Customer receipt"
            legs = [
                (1000, amount_pence, 0),
                (1100, 0, amount_pence),
            ]

        for line_no, (account_code, debit_pence, credit_pence) in enumerate(legs, start=1):
            rows.append({
                "entry_id": entry_id,
                "line_no": line_no,
                "posted_at": posted_at,
                "account_code": account_code,
                "debit_pence": debit_pence,
                "credit_pence": credit_pence,
                "user_id": user_id,
                "approver_id": approver_id,
                "description": description,
            })

    entry_id = ordinary_count
    payroll_user = "U08"

    for payroll_date in payroll_dates:
        for salary_pence in SALARY_PENCE.values():
            entry_id += 1
            posted_at = payroll_date.replace(
                hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
                minute=rng.randrange(60),
                second=0,
                microsecond=0,
            )
            user_id = payroll_user
            approver_id = rng.choice(APPROVERS)
            assert approver_id != user_id
            legs = [
                (7000, salary_pence, 0),
                (1000, 0, salary_pence),
            ]

            for line_no, (account_code, debit_pence, credit_pence) in enumerate(legs, start=1):
                rows.append({
                    "entry_id": entry_id,
                    "line_no": line_no,
                    "posted_at": posted_at,
                    "account_code": account_code,
                    "debit_pence": debit_pence,
                    "credit_pence": credit_pence,
                    "user_id": user_id,
                    "approver_id": approver_id,
                    "description": "Payroll",
                })

    for settlement_date in vat_settlement_dates:
        entry_id += 1
        quarter = (settlement_date.year, (settlement_date.month - 1) // 3 + 1)
        amount_pence = quarterly_vat.get(quarter, 0)
        posted_at = settlement_date.replace(
            hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
            minute=rng.randrange(60),
            second=0,
            microsecond=0,
        )
        user_id = rng.choice(USERS)
        approver_id = rng.choice(APPROVERS)
        assert approver_id != user_id
        legs = [
            (2100, amount_pence, 0),
            (1000, 0, amount_pence),
        ]

        for line_no, (account_code, debit_pence, credit_pence) in enumerate(legs, start=1):
            rows.append({
                "entry_id": entry_id,
                "line_no": line_no,
                "posted_at": posted_at,
                "account_code": account_code,
                "debit_pence": debit_pence,
                "credit_pence": credit_pence,
                "user_id": user_id,
                "approver_id": approver_id,
                "description": "VAT settlement",
            })

    ledger = pd.DataFrame(rows, columns=columns)
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)
    return ledger

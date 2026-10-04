from datetime import datetime, timedelta
import random
import pandas as pd
from ledger_audit.chart_of_accounts import accounts_of_type
import calendar


USERS = ["U01", "U02", "U03", "U04", "U05", "U06", "U07", "U08"]
APPROVERS = ["A01", "A02", "A03"]
CUSTOMERS_IDS = [f"C{number:02d}" for number in range(1, 21)]
VENDOR_IDS = [f"V{number:02d}" for number in range(1, 16)]
SEASONALITY = {
    1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
    7: 0.8, 8: 0.8, 9: 1.1, 10: 1.1, 11: 1.3, 12: 1.4,
}
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
    columns = [
        "entry_id",
        "line_no",
        "posted_at",
        "account_code",
        "debit_pence",
        "credit_pence",
        "user_id",
        "approver_id",
        "description",
        "customer_id",
        "vendor_id",
    ]
    expense_accounts = accounts_of_type("expense")
    open_sales_invoices = []
    open_purchase_invoices = []
    next_invoice_id = 1

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

    months_in_range = (
        (last_random_date.year - start.year) * 12
        + (last_random_date.month - start.month)
        + 1
    )
    scheduled_count = (
        len(payroll_dates) * len(USERS)
        + len(vat_settlement_dates)
        + months_in_range * 2
    )

    if n_entries < scheduled_count:
        raise ValueError(
            "n_entries must be at least the number of scheduled entries")

    ordinary_count = n_entries - scheduled_count
    quarterly_vat: dict[tuple[int, int], int] = {}
    entry_id = 1

    for _ in range(ordinary_count):
        while True:
            posted_at = start + timedelta(days=rng.randrange(days))
            if posted_at.weekday() < 5:
                posted_at = posted_at.replace(
                    hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
                    minute=rng.randrange(60),
                    second=0,
                    microsecond=0,
                )
                break

        user_id = rng.choice(USERS)
        approver_id = rng.choice(APPROVERS)
        assert approver_id != user_id
        amount_pence = max(100, int(rng.lognormvariate(6.0, 1.0) * 100))

        valid_events = ["sale", "expense"]
        if open_sales_invoices:
            valid_events.append("customer_receipt")
        if open_purchase_invoices:
            valid_events.append("supplier_payment")
        event_type = rng.choice(valid_events)

        if event_type == "sale":
            customer_id = rng.choice(CUSTOMERS_IDS)
            invoice = {
                "invoice_id": next_invoice_id,
                "customer_id": customer_id,
                "amount_pence": amount_pence,
                "issued_at": posted_at,
            }
            next_invoice_id += 1
            open_sales_invoices.append(invoice)

            description = "Sale"
            customer_id_value = customer_id
            vendor_id_value = ""
            legs = [
                (1100, amount_pence, 0),
                (4000, 0, amount_pence),
            ]
        elif event_type == "expense":
            vendor_id = rng.choice(VENDOR_IDS)
            invoice = {
                "invoice_id": next_invoice_id,
                "vendor_id": vendor_id,
                "amount_pence": amount_pence,
                "issued_at": posted_at,
            }
            next_invoice_id += 1
            open_purchase_invoices.append(invoice)

            description = "Expense"
            expense_account = rng.choice(expense_accounts)
            vat_pence = round(amount_pence * VAT_RATE)
            quarter = (posted_at.year, (posted_at.month - 1) // 3 + 1)
            quarterly_vat[quarter] = quarterly_vat.get(quarter, 0) + vat_pence

            customer_id_value = ""
            vendor_id_value = vendor_id
            legs = [
                (expense_account.code, amount_pence, 0),
                (1200, vat_pence, 0),
                (2000, 0, amount_pence + vat_pence),
            ]
        elif event_type == "supplier_payment":
            invoice = rng.choice(open_purchase_invoices)
            open_purchase_invoices.remove(invoice)
            amount_pence = invoice["amount_pence"]

            description = "Supplier payment"
            customer_id_value = ""
            vendor_id_value = invoice["vendor_id"]
            legs = [
                (2000, amount_pence, 0),
                (1000, 0, amount_pence),
            ]
        else:
            invoice = rng.choice(open_sales_invoices)
            open_sales_invoices.remove(invoice)
            amount_pence = invoice["amount_pence"]

            description = "Customer receipt"
            customer_id_value = invoice["customer_id"]
            vendor_id_value = ""
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
                "customer_id": customer_id_value,
                "vendor_id": vendor_id_value,
            })

        entry_id += 1

    for payroll_date in payroll_dates:
        for salary_pence in SALARY_PENCE.values():
            posted_at = payroll_date.replace(
                hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
                minute=rng.randrange(60),
                second=0,
                microsecond=0,
            )
            user_id = "U08"
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
                    "customer_id": "",
                    "vendor_id": "",
                })
            entry_id += 1

    month_cursor = datetime(start.year, start.month, 1)
    final_month = datetime(last_random_date.year, last_random_date.month, 1)

    while month_cursor <= final_month:
        last_day = calendar.monthrange(
            month_cursor.year, month_cursor.month)[1]
        month_end = datetime(month_cursor.year, month_cursor.month, last_day)

        while month_end.weekday() >= 5:
            month_end -= timedelta(days=1)

        posted_at = month_end.replace(
            hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
            minute=rng.randrange(60),
            second=0,
            microsecond=0,
        )
        user_id = rng.choice(USERS)
        approver_id = rng.choice(APPROVERS)
        assert approver_id != user_id

        rows.append({
            "entry_id": entry_id,
            "line_no": 1,
            "posted_at": posted_at,
            "account_code": 6500,
            "debit_pence": 50000,
            "credit_pence": 0,
            "user_id": user_id,
            "approver_id": approver_id,
            "description": "Depreciation",
            "customer_id": "",
            "vendor_id": "",
        })
        rows.append({
            "entry_id": entry_id,
            "line_no": 2,
            "posted_at": posted_at,
            "account_code": 1300,
            "debit_pence": 0,
            "credit_pence": 50000,
            "user_id": user_id,
            "approver_id": approver_id,
            "description": "Depreciation",
            "customer_id": "",
            "vendor_id": "",
        })
        entry_id += 1

        accrual_amount = rng.randint(10000, 80000)
        posted_at = month_end.replace(
            hour=rng.randrange(WORKING_HOUR_START, WORKING_HOUR_END),
            minute=rng.randrange(60),
            second=0,
            microsecond=0,
        )
        user_id = rng.choice(USERS)
        approver_id = rng.choice(APPROVERS)
        assert approver_id != user_id

        rows.append({
            "entry_id": entry_id,
            "line_no": 1,
            "posted_at": posted_at,
            "account_code": 6300,
            "debit_pence": accrual_amount,
            "credit_pence": 0,
            "user_id": user_id,
            "approver_id": approver_id,
            "description": "Accrual",
            "customer_id": "",
            "vendor_id": "",
        })
        rows.append({
            "entry_id": entry_id,
            "line_no": 2,
            "posted_at": posted_at,
            "account_code": 2200,
            "debit_pence": 0,
            "credit_pence": accrual_amount,
            "user_id": user_id,
            "approver_id": approver_id,
            "description": "Accrual",
            "customer_id": "",
            "vendor_id": "",
        })
        entry_id += 1

        if month_cursor.month == 12:
            month_cursor = datetime(month_cursor.year + 1, 1, 1)
        else:
            month_cursor = datetime(
                month_cursor.year, month_cursor.month + 1, 1)

    for settlement_date in vat_settlement_dates:
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
                "customer_id": "",
                "vendor_id": "",
            })
        entry_id += 1

    ledger = pd.DataFrame(rows, columns=columns)
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)
    return ledger

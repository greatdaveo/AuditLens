
import random
import pandas as pd

from ledger_audit.anomalies import inject_duplicate_payment, inject_self_approved, inject_below_limit, inject_odd_timing, inject_round_number, inject_rare_pairing, inject_all
from ledger_audit.validate import unbalanced_entries
from ledger_audit.chart_of_accounts import accounts_of_type
from ledger_audit.generator import generate_ledger


def test_self_approval_changes_approver_without_unbalancing_entry():
    ledger = pd.DataFrame([
        {
            "entry_id": 1,
            "line_no": 1,
            "account_code": 1100,
            "debit_pence": 10000,
            "credit_pence": 0,
            "user_id": "U01",
            "approver_id": "A01",
        },
        {
            "entry_id": 1,
            "line_no": 2,
            "account_code": 4000,
            "debit_pence": 0,
            "credit_pence": 10000,
            "user_id": "U01",
            "approver_id": "A01",
        },
    ])

    modified_ledger, changed_entry_ids = inject_self_approved(
        ledger,
        random.Random(7),
        n=1,
    )

    assert set(changed_entry_ids) == {1}

    entry_rows = modified_ledger.loc[modified_ledger["entry_id"] == 1]

    assert (entry_rows["user_id"] == entry_rows["approver_id"]).all()

    assert unbalanced_entries(modified_ledger).empty

    assert (ledger["approver_id"] == "A01").all()


def test_duplicate_payment_copies_balanced_entry_with_new_id_and_later_date():

    posted_at = pd.Timestamp("2024-01-08 10:30:00")

    ledger = pd.DataFrame([
        {
            "entry_id": 7,
            "line_no": 1,
            "posted_at": posted_at,
            "account_code": 2000,
            "debit_pence": 10000,
            "credit_pence": 0,
            "user_id": "U02",
            "approver_id": "A02",
            "description": "Supplier payment",
            "customer_id": "",
            "vendor_id": "V01",
        },
        {
            "entry_id": 7,
            "line_no": 2,
            "posted_at": posted_at,
            "account_code": 1000,
            "debit_pence": 0,
            "credit_pence": 10000,
            "user_id": "U02",
            "approver_id": "A02",
            "description": "Supplier payment",
            "customer_id": "",
            "vendor_id": "V01",
        },
    ])

    modified_ledger, new_entry_ids = inject_duplicate_payment(
        ledger,
        random.Random(12),
        n=1,
    )

    assert len(new_entry_ids) == 1

    duplicate_entry_id = new_entry_ids[0]

    assert duplicate_entry_id != 7

    original_rows = modified_ledger.loc[modified_ledger["entry_id"] == 7]

    duplicate_rows = modified_ledger.loc[modified_ledger["entry_id"]
                                         == duplicate_entry_id]

    assert len(duplicate_rows) == 2
    assert duplicate_rows["vendor_id"].eq("V01").all()
    assert duplicate_rows["description"].eq("Supplier payment").all()

    copied_columns = ["line_no", "account_code",
                      "debit_pence", "credit_pence", "vendor_id"]
    pd.testing.assert_frame_equal(
        original_rows[copied_columns].reset_index(drop=True),
        duplicate_rows[copied_columns].reset_index(drop=True),
    )

    day_offsets = (duplicate_rows["posted_at"] - posted_at).dt.days

    assert day_offsets.between(1, 5).all()
    assert unbalanced_entries(modified_ledger).empty
    assert len(ledger) == 2


def test_below_limit_changes_expense_and_recalculates_vat_and_payable():
    ledger = pd.DataFrame([
        {
            "entry_id": 13,
            "line_no": 1,
            "account_code": 6300,
            "debit_pence": 2_000_000,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 13,
            "line_no": 2,
            "account_code": 1200,
            "debit_pence": 400_000,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 13,
            "line_no": 3,
            "account_code": 2000,
            "debit_pence": 0,
            "credit_pence": 2_400_000,
            "description": "Expense",
        },
    ])

    modified_ledger, changed_entry_ids = inject_below_limit(
        ledger,
        random.Random(21),
        n=1,
    )

    assert changed_entry_ids == [13]

    entry_rows = modified_ledger.loc[modified_ledger["entry_id"] == 13]
    expense_amount = int(
        entry_rows.loc[entry_rows["account_code"]
                       == 6300, "debit_pence"].iloc[0]
    )
    vat_amount = int(
        entry_rows.loc[entry_rows["account_code"]
                       == 1200, "debit_pence"].iloc[0]
    )
    payable_amount = int(
        entry_rows.loc[entry_rows["account_code"]
                       == 2000, "credit_pence"].iloc[0]
    )

    assert 970_000 <= expense_amount <= 999_900
    assert vat_amount == round(expense_amount * 0.20)
    assert payable_amount == expense_amount + vat_amount
    assert unbalanced_entries(modified_ledger).empty
    assert int(ledger.loc[ledger["account_code"] ==
               6300, "debit_pence"].iloc[0]) == 2_000_000


def test_odd_timing_moves_entry_to_an_allowed_unusual_time():
    original_time = pd.Timestamp("2024-01-08 10:30:00")

    ledger = pd.DataFrame([
        {
            "entry_id": 25,
            "line_no": 1,
            "posted_at": original_time,
            "account_code": 1100,
            "debit_pence": 15000,
            "credit_pence": 0,
            "user_id": "U01",
            "approver_id": "A01",
        },
        {
            "entry_id": 25,
            "line_no": 2,
            "posted_at": original_time,
            "account_code": 4000,
            "debit_pence": 0,
            "credit_pence": 15000,
            "user_id": "U01",
            "approver_id": "A01",
        },
    ])

    modified_ledger, changed_entry_ids = inject_odd_timing(
        ledger,
        random.Random(31),
        n=1,
    )
    assert changed_entry_ids == [25]

    changed_rows = modified_ledger.loc[modified_ledger["entry_id"] == 25]
    changed_time = changed_rows["posted_at"].iloc[0]

    assert changed_rows["posted_at"].eq(changed_time).all()
    assert changed_time != original_time

    if changed_time.weekday() >= 5:
        assert changed_time.isocalendar(
        )[:2] == original_time.isocalendar()[:2]
    else:
        assert changed_time.date() == original_time.date()
        assert changed_time.hour < 6 or changed_time.hour >= 22

    assert unbalanced_entries(modified_ledger).empty
    assert ledger["posted_at"].eq(original_time).all()


def test_round_number_changes_expense_to_multiple_of_100_pounds():
    ledger = pd.DataFrame([
        {
            "entry_id": 41,
            "line_no": 1,
            "account_code": 6300,
            "debit_pence": 2_055_100,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 41,
            "line_no": 2,
            "account_code": 1200,
            "debit_pence": 411_020,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 41,
            "line_no": 3,
            "account_code": 2000,
            "debit_pence": 0,
            "credit_pence": 2_466_120,
            "description": "Expense",
        },
    ])

    modified_ledger, changed_entry_ids = inject_round_number(
        ledger,
        random.Random(44),
        n=1,
    )
    assert changed_entry_ids == [41]

    entry_rows = modified_ledger.loc[modified_ledger["entry_id"] == 41]
    expense_amount = int(
        entry_rows.loc[entry_rows["account_code"]
                       == 6300, "debit_pence"].iloc[0]
    )

    vat_amount = int(
        entry_rows.loc[entry_rows["account_code"]
                       == 1200, "debit_pence"].iloc[0]
    )

    payable_amount = int(
        entry_rows.loc[entry_rows["account_code"]
                       == 2000, "credit_pence"].iloc[0]
    )

    assert expense_amount != 2_055_100
    assert expense_amount % 10_000 == 0
    assert vat_amount == round(expense_amount * 0.20)
    assert payable_amount == expense_amount + vat_amount
    assert unbalanced_entries(modified_ledger).empty
    assert int(ledger.loc[ledger["account_code"] ==
               6300, "debit_pence"].iloc[0]) == 2_055_100


def test_rare_pairing_changes_expense_account_to_another_expense_account():
    ledger = pd.DataFrame([
        {
            "entry_id": 52,
            "line_no": 1,
            "account_code": 6200,
            "debit_pence": 100_000,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 52,
            "line_no": 2,
            "account_code": 1200,
            "debit_pence": 20_000,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 52,
            "line_no": 3,
            "account_code": 2000,
            "debit_pence": 0,
            "credit_pence": 120_000,
            "description": "Expense",
        },
    ])

    expense_account_codes = {
        account.code for account in accounts_of_type("expense")
    }

    modified_ledger, changed_entry_ids = inject_rare_pairing(
        ledger,

        random.Random(52),
        n=1,
    )
    assert changed_entry_ids == [52]

    changed_rows = modified_ledger.loc[modified_ledger["entry_id"] == 52]
    new_expense_code = int(
        changed_rows.loc[changed_rows["debit_pence"] > 0]
        .loc[lambda rows: rows["account_code"] != 1200, "account_code"]
        .iloc[0]
    )
    assert new_expense_code in expense_account_codes
    assert new_expense_code != 6200
    assert changed_rows.loc[changed_rows["account_code"]
                            == 1200, "debit_pence"].iloc[0] == 20_000
    assert changed_rows.loc[changed_rows["account_code"]
                            == 2000, "credit_pence"].iloc[0] == 120_000
    assert unbalanced_entries(modified_ledger).empty
    assert ledger.loc[ledger["entry_id"] == 52, "account_code"].iloc[0] == 6200


def test_inject_all_labels_every_entry_once_and_keeps_ledger_balanced():
    ledger = generate_ledger(
        n_entries=2_000,
        seed=42,
        start=pd.Timestamp("2024-01-01").to_pydatetime(),
        days=365,
    )

    rates = {
        "duplicate_payment": 0.0015,
        "below_limit": 0.0015,
        "odd_timing": 0.0015,
        "self_approved": 0.001,
        "round_number": 0.0015,
        "rare_pairing": 0.001,
    }

    modified_ledger, labels = inject_all(
        ledger,
        seed=99,
        rates=rates,
    )

    assert labels.columns.tolist() == [
        "entry_id",
        "is_anomaly",
        "anomaly_type",
    ]
    assert labels["entry_id"].is_unique
    assert set(labels["entry_id"]) == set(modified_ledger["entry_id"])
    assert labels["is_anomaly"].dtype == bool
    assert labels.loc[~labels["is_anomaly"], "anomaly_type"].eq("").all()
    assert labels.loc[labels["is_anomaly"], "anomaly_type"].isin(rates).all()
    assert unbalanced_entries(modified_ledger).empty

    original_entry_count = ledger["entry_id"].nunique()

    for anomaly_name, rate in rates.items():
        expected_count = round(original_entry_count * rate)
        actual_count = int((labels["anomaly_type"] == anomaly_name).sum())
        assert actual_count == expected_count

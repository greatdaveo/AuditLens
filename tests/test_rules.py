import pandas as pd
from math import log10

from ledger_audit.rules import rule_self_approved, rule_odd_timing, rule_duplicate, rule_below_limit, rule_round_number, rule_benfords_law, run_all_rules


def test_self_approved_rule_flags_matching_users_and_ignores_clean_entries():
    ledger_with_one_self_approved = pd.DataFrame([
        {"entry_id": 100, "user_id": "U01", "approver_id": "U01"},
        {"entry_id": 101, "user_id": "U02", "approver_id": "A01"},
        {"entry_id": 102, "user_id": "U03", "approver_id": "A02"},
    ])

    clean_ledger = pd.DataFrame([
        {"entry_id": 202, "user_id": "U02", "approver_id": "A02"},
        {"entry_id": 203, "user_id": "U03", "approver_id": "A03"},
    ])

    flagged = rule_self_approved(ledger_with_one_self_approved)

    assert flagged["entry_id"].tolist() == [100]
    assert flagged.columns.tolist() == ["entry_id", "reason"]
    assert flagged["reason"].str.len().gt(0).all()
    assert rule_self_approved(clean_ledger).empty


def test_odd_timing_rule_flags_weekend_and_out_of_hours_entries():
    ledger_with_odd_times = pd.DataFrame([
        {
            "entry_id": 301,
            "posted_at": pd.Timestamp("2024-01-06 10:00:00"),
        },
        {
            "entry_id": 302,
            "posted_at": pd.Timestamp("2024-01-08 05:30:00"),
        },
        {
            "entry_id": 303,
            "posted_at": pd.Timestamp("2024-01-08 10:00:00"),
        },
    ])

    clean_ledger = pd.DataFrame([
        {"entry_id": 401, "posted_at": pd.Timestamp("2024-01-08 06:00:00")},
        {"entry_id": 402, "posted_at": pd.Timestamp("2024-01-09 14:30:00")},
        {"entry_id": 403, "posted_at": pd.Timestamp("2024-01-10 21:59:00")},
    ])

    flagged = rule_odd_timing(ledger_with_odd_times)

    assert flagged["entry_id"].tolist() == [301, 302]
    assert flagged.columns.tolist() == ["entry_id", "reason"]
    assert flagged["reason"].str.len().gt(0).all()
    assert rule_odd_timing(clean_ledger).empty


def test_duplicate_rule_flags_close_matching_vendor_payments():
    ledger = pd.DataFrame([
        {
            "entry_id": 501,
            "line_no": 1,
            "posted_at": pd.Timestamp("2024-01-08 10:00:00"),
            "account_code": 2000,
            "debit_pence": 10_000,
            "credit_pence": 0,
            "vendor_id": "V01",
            "description": "Supplier payment",
        },
        {
            "entry_id": 501,
            "line_no": 2,
            "posted_at": pd.Timestamp("2024-01-08 10:00:00"),
            "account_code": 1000,
            "debit_pence": 0,
            "credit_pence": 10_000,
            "vendor_id": "V01",
            "description": "Supplier payment",
        },
        {
            "entry_id": 502,
            "line_no": 1,
            "posted_at": pd.Timestamp("2024-01-11 11:00:00"),
            "account_code": 2000,
            "debit_pence": 10_000,
            "credit_pence": 0,
            "vendor_id": "V01",
            "description": "Supplier payment",
        },
        {
            "entry_id": 502,
            "line_no": 2,
            "posted_at": pd.Timestamp("2024-01-11 11:00:00"),
            "account_code": 1000,
            "debit_pence": 0,
            "credit_pence": 10_000,
            "vendor_id": "V01",
            "description": "Supplier payment",
        },
        {
            "entry_id": 503,
            "line_no": 1,
            "posted_at": pd.Timestamp("2024-01-09 12:00:00"),
            "account_code": 2000,
            "debit_pence": 10_000,
            "credit_pence": 0,
            "vendor_id": "V02",
            "description": "Supplier payment",
        },
        {
            "entry_id": 503,
            "line_no": 2,
            "posted_at": pd.Timestamp("2024-01-09 12:00:00"),
            "account_code": 1000,
            "debit_pence": 0,
            "credit_pence": 10_000,
            "vendor_id": "V02",
            "description": "Supplier payment",
        },
    ])

    flagged = rule_duplicate(ledger)

    assert flagged["entry_id"].tolist() == [501, 502]
    assert flagged.columns.tolist() == ["entry_id", "reason"]
    assert flagged["reason"].str.len().gt(0).all()

    clean_ledger = ledger.copy()
    clean_ledger.loc[clean_ledger["entry_id"] == 502, "posted_at"] = pd.Timestamp(
        "2024-01-20 11:00:00"
    )

    assert rule_duplicate(clean_ledger).empty


def test_below_limit_rule_checks_net_expense_amount():
    below_limit_ledger = pd.DataFrame([
        {"entry_id": 601, "account_code": 6300,
            "debit_pence": 980_000, "credit_pence": 0},
        {"entry_id": 601, "account_code": 1200,
            "debit_pence": 196_000, "credit_pence": 0},
        {"entry_id": 601, "account_code": 2000,
            "debit_pence": 0, "credit_pence": 1_176_000},
    ])

    ordinary_ledger = pd.DataFrame([
        {"entry_id": 602, "account_code": 6300,
            "debit_pence": 1_200_000, "credit_pence": 0},
        {"entry_id": 602, "account_code": 1200,
            "debit_pence": 240_000, "credit_pence": 0},
        {"entry_id": 602, "account_code": 2000,
            "debit_pence": 0, "credit_pence": 1_440_000},
    ])

    flagged = rule_below_limit(below_limit_ledger)
    assert flagged["entry_id"].tolist() == [601]
    assert flagged.columns.tolist() == ["entry_id", "reason"]
    assert flagged["reason"].str.len().gt(0).all()
    assert rule_below_limit(ordinary_ledger).empty


def test_round_number_rule_checks_net_expense_amount():
    ledger_with_round_expense = pd.DataFrame([
        {
            "entry_id": 701,
            "account_code": 6300,
            "debit_pence": 300_000,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 701,
            "account_code": 1200,
            "debit_pence": 60_000,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 701,
            "account_code": 2000,
            "debit_pence": 0,
            "credit_pence": 360_000,
            "description": "Expense",
        },
        {
            "entry_id": 702,
            "account_code": 6300,
            "debit_pence": 301_234,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 702,
            "account_code": 1200,
            "debit_pence": 60_247,
            "credit_pence": 0,
            "description": "Expense",
        },
        {
            "entry_id": 702,
            "account_code": 2000,
            "debit_pence": 0,
            "credit_pence": 361_481,
            "description": "Expense",
        },
    ])

    flagged = rule_round_number(ledger_with_round_expense)

    assert flagged["entry_id"].tolist() == [701]
    assert flagged.columns.tolist() == ["entry_id", "reason"]
    assert flagged["reason"].str.len().gt(0).all()


def test_benfords_law_rule_flags_skewed_digits_but_accepts_expected_distribution():
    skewed_ledger = pd.DataFrame([
        {"entry_id": 801, "debit_pence": 200_000, "credit_pence": 0},
        {"entry_id": 802, "debit_pence": 250_000, "credit_pence": 0},
        {"entry_id": 803, "debit_pence": 900_000, "credit_pence": 0},
    ])

    flagged = rule_benfords_law(skewed_ledger)

    assert set(flagged["entry_id"]) == {801, 802, 803}
    assert flagged.columns.tolist() == ["entry_id", "reason"]
    assert flagged["reason"].str.len().gt(0).all()

    total_entries = 1_000
    digit_counts = {
        digit: round(log10(1 + 1 / digit) * total_entries)
        for digit in range(1, 10)
    }
    digit_counts[9] += total_entries - sum(digit_counts.values())

    clean_amounts = []
    for digit, count in digit_counts.items():
        clean_amounts.extend(
            digit * 100_000 + offset
            for offset in range(count)
        )

    clean_ledger = pd.DataFrame({
        "entry_id": range(total_entries),
        "debit_pence": clean_amounts,
        "credit_pence": [0] * total_entries,
    })

    assert rule_benfords_law(clean_ledger).empty


def test_run_all_rules_combines_flags_with_rule_names():
    ledger = pd.DataFrame([
        {
            "entry_id": 901,
            "posted_at": pd.Timestamp("2024-01-08 10:00:00"),
            "account_code": 1100,
            "debit_pence": 10_000,
            "credit_pence": 0,
            "user_id": "U01",
            "approver_id": "U01",
            "description": "Sale",
            "vendor_id": "",
        },
        {
            "entry_id": 902,
            "posted_at": pd.Timestamp("2024-01-06 10:00:00"),
            "account_code": 6300,
            "debit_pence": 980_000,
            "credit_pence": 0,
            "user_id": "U02",
            "approver_id": "A01",
            "description": "Expense",
            "vendor_id": "V01",
        },
        {
            "entry_id": 903,
            "posted_at": pd.Timestamp("2024-01-08 10:00:00"),
            "account_code": 2000,
            "debit_pence": 10_000,
            "credit_pence": 0,
            "user_id": "U03",
            "approver_id": "A02",
            "description": "Supplier payment",
            "vendor_id": "V01",
        },
    ])

    results = run_all_rules(ledger)

    expected_columns = ["entry_id", "reason", "rule_name"]
    expected_rule_names = {
        "benfords_law",
        "duplicate",
        "below_limit",
        "odd_timing",
        "self_approved",
        "round_number",
    }

    assert results.columns.tolist() == expected_columns
    assert "self_approved" in set(results["rule_name"])
    assert results["rule_name"].isin(expected_rule_names).all()
    assert not results.duplicated(["entry_id", "rule_name"]).any()
    assert results["reason"].str.len().gt(0).all()

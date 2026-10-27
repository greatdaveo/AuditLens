import random
import pandas as pd
from datetime import timedelta

from ledger_audit.generator import VAT_RATE
from ledger_audit.chart_of_accounts import accounts_of_type


APPROVAL_LIMIT_PENCE = 1_000_000


def inject_self_approved(
    ledger: pd.DataFrame,
    rng: random.Random,
    n: int,
) -> tuple[pd.DataFrame, list[int]]:

    modified_ledger = ledger.copy()

    entry_ids = modified_ledger["entry_id"].drop_duplicates().tolist()

    changed_entry_ids = rng.sample(entry_ids, n)

    for entry_id in changed_entry_ids:

        entry_mask = modified_ledger["entry_id"] == entry_id
        modified_ledger.loc[entry_mask, "approver_id"] = modified_ledger.loc[

            entry_mask, "user_id"
        ]

    return modified_ledger, changed_entry_ids


def inject_duplicate_payment(
    ledger: pd.DataFrame,
    rng: random.Random,
    n: int,
) -> tuple[pd.DataFrame, list[int]]:

    modified_ledger = ledger.copy()

    payment_rows = modified_ledger.loc[
        modified_ledger["description"] == "Supplier payment"
    ]

    eligible_entry_ids = payment_rows["entry_id"].drop_duplicates().tolist()

    selected_entry_ids = rng.sample(eligible_entry_ids, n)

    next_entry_id = int(modified_ledger["entry_id"].max()) + 1

    duplicate_rows = []
    new_entry_ids = []

    for original_entry_id in selected_entry_ids:
        original_rows = modified_ledger.loc[
            modified_ledger["entry_id"] == original_entry_id
        ].copy()

        original_posted_at = original_rows["posted_at"].iloc[0]
        days_later = rng.randint(1, 5)
        copied_rows = original_rows.copy()
        copied_rows["entry_id"] = next_entry_id
        new_entry_ids.append(next_entry_id)
        copied_rows["posted_at"] = original_posted_at + \
            timedelta(days=days_later)
        duplicate_rows.append(copied_rows)
        next_entry_id += 1

    if duplicate_rows:
        modified_ledger = pd.concat(
            [modified_ledger, *duplicate_rows],

            ignore_index=True,
        )

    return modified_ledger, new_entry_ids


def inject_below_limit(
    ledger: pd.DataFrame,
    rng: random.Random,
    n: int,
) -> tuple[pd.DataFrame, list[int]]:

    modified_ledger = ledger.copy()

    expense_rows = modified_ledger.loc[
        modified_ledger["description"] == "Expense"
    ]

    eligible_entry_ids = expense_rows["entry_id"].drop_duplicates().tolist()

    changed_entry_ids = rng.sample(eligible_entry_ids, n)

    for entry_id in changed_entry_ids:

        entry_mask = modified_ledger["entry_id"] == entry_id

        expense_line_mask = (
            entry_mask
            & (modified_ledger["debit_pence"] > 0)
            & (modified_ledger["account_code"] != 1200)
        )

        vat_line_mask = entry_mask & (modified_ledger["account_code"] == 1200)

        payable_line_mask = entry_mask & (
            modified_ledger["account_code"] == 2000)

        new_expense_amount = rng.randint(970_000, 999_900)

        new_vat_amount = round(new_expense_amount * VAT_RATE)

        new_payable_amount = new_expense_amount + new_vat_amount

        modified_ledger.loc[expense_line_mask,
                            "debit_pence"] = new_expense_amount
        modified_ledger.loc[vat_line_mask, "debit_pence"] = new_vat_amount
        modified_ledger.loc[payable_line_mask,
                            "credit_pence"] = new_payable_amount

    return modified_ledger, changed_entry_ids


def inject_odd_timing(
    ledger: pd.DataFrame,
    rng: random.Random,
    n: int,
) -> tuple[pd.DataFrame, list[int]]:
    modified_ledger = ledger.copy()
    entry_ids = modified_ledger["entry_id"].drop_duplicates().tolist()
    changed_entry_ids = rng.sample(entry_ids, n)

    for entry_id in changed_entry_ids:
        entry_mask = modified_ledger["entry_id"] == entry_id
        original_posted_at = modified_ledger.loc[entry_mask,
                                                 "posted_at"].iloc[0]
        choose_weekend = rng.choice([True, False])

        if choose_weekend:
            week_start = original_posted_at - \
                timedelta(days=original_posted_at.weekday())
            weekend_offset = rng.choice([5, 6])
            new_posted_at = week_start + timedelta(days=weekend_offset)
        else:
            choose_early = rng.choice([True, False])

            if choose_early:
                unusual_hour = rng.randrange(0, 6)
            else:
                unusual_hour = rng.randrange(22, 24)

            new_posted_at = original_posted_at.replace(
                hour=unusual_hour,
                minute=rng.randrange(60),
                second=0,
                microsecond=0,
            )

        modified_ledger.loc[entry_mask, "posted_at"] = new_posted_at

    return modified_ledger, changed_entry_ids


def inject_round_number(
    ledger: pd.DataFrame,
    rng: random.Random,
    n: int,
) -> tuple[pd.DataFrame, list[int]]:
    modified_ledger = ledger.copy()

    expense_rows = modified_ledger.loc[
        modified_ledger["description"] == "Expense"
    ]
    eligible_entry_ids = expense_rows["entry_id"].drop_duplicates().tolist()
    changed_entry_ids = rng.sample(eligible_entry_ids, n)

    for entry_id in changed_entry_ids:
        entry_mask = modified_ledger["entry_id"] == entry_id

        expense_line_mask = (
            entry_mask
            & (modified_ledger["debit_pence"] > 0)
            & (modified_ledger["account_code"] != 1200)
        )

        vat_line_mask = entry_mask & (modified_ledger["account_code"] == 1200)

        payable_line_mask = entry_mask & (
            modified_ledger["account_code"] == 2000)

        new_expense_amount = rng.randint(1, 1000) * 10_000
        new_vat_amount = round(new_expense_amount * VAT_RATE)
        new_payable_amount = new_expense_amount + new_vat_amount

        modified_ledger.loc[expense_line_mask,
                            "debit_pence"] = new_expense_amount
        modified_ledger.loc[vat_line_mask, "debit_pence"] = new_vat_amount
        modified_ledger.loc[payable_line_mask,
                            "credit_pence"] = new_payable_amount

    return modified_ledger, changed_entry_ids


def inject_rare_pairing(
    ledger: pd.DataFrame,
    rng: random.Random,
    n: int,
) -> tuple[pd.DataFrame, list[int]]:
    modified_ledger = ledger.copy()

    expense_account_codes = [
        account.code for account in accounts_of_type("expense")
    ]

    expense_rows = modified_ledger.loc[
        modified_ledger["description"] == "Expense"
    ]
    eligible_entry_ids = expense_rows["entry_id"].drop_duplicates().tolist()
    changed_entry_ids = rng.sample(eligible_entry_ids, n)

    for entry_id in changed_entry_ids:
        entry_mask = modified_ledger["entry_id"] == entry_id
        expense_line_mask = (
            entry_mask
            & (modified_ledger["debit_pence"] > 0)
            & (modified_ledger["account_code"] != 1200)
        )

        current_account_code = int(
            modified_ledger.loc[expense_line_mask, "account_code"].iloc[0]
        )
        alternative_codes = [
            code for code in expense_account_codes if code != current_account_code
        ]
        new_account_code = rng.choice(alternative_codes)

        modified_ledger.loc[expense_line_mask,
                            "account_code"] = new_account_code

    return modified_ledger, changed_entry_ids


def inject_all(
    ledger: pd.DataFrame,
    seed: int,
    rates: dict[str, float],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = random.Random(seed)
    modified_ledger = ledger.copy()
    original_entry_count = ledger["entry_id"].nunique()
    used_entry_ids = set()
    anomaly_type_by_entry = {}
    next_entry_id = int(modified_ledger["entry_id"].max()) + 1

    injection_specs = {
        "duplicate_payment": (inject_duplicate_payment, "Supplier payment"),
        "below_limit": (inject_below_limit, "Expense"),
        "odd_timing": (inject_odd_timing, None),
        "self_approved": (inject_self_approved, None),
        "round_number": (inject_round_number, "Expense"),
        "rare_pairing": (inject_rare_pairing, "Expense"),
    }

    for anomaly_name, (injector, required_description) in injection_specs.items():
        requested_count = int(
            round(original_entry_count * rates[anomaly_name]))

        if requested_count == 0:
            continue

        eligible_rows = modified_ledger

        if required_description is not None:
            eligible_rows = modified_ledger.loc[
                modified_ledger["description"] == required_description
            ]

        eligible_entry_ids = [
            entry_id
            for entry_id in eligible_rows["entry_id"].drop_duplicates().tolist()
            if entry_id not in used_entry_ids
        ]
        selected_entry_ids = rng.sample(eligible_entry_ids, requested_count)
        selected_rows = modified_ledger.loc[
            modified_ledger["entry_id"].isin(selected_entry_ids)
        ].copy()

        injected_rows, changed_entry_ids = injector(
            selected_rows,
            rng,
            requested_count,
        )

        if anomaly_name == "duplicate_payment":
            for generated_entry_id in changed_entry_ids:
                duplicate_rows = injected_rows.loc[
                    injected_rows["entry_id"] == generated_entry_id
                ].copy()
                duplicate_rows["entry_id"] = next_entry_id
                modified_ledger = pd.concat(
                    [modified_ledger, duplicate_rows],
                    ignore_index=True,
                )
                anomaly_type_by_entry[next_entry_id] = anomaly_name
                used_entry_ids.add(next_entry_id)
                next_entry_id += 1

            used_entry_ids.update(selected_entry_ids)
        else:
            changed_rows = injected_rows.loc[
                injected_rows["entry_id"].isin(changed_entry_ids)
            ]
            modified_ledger = modified_ledger.loc[
                ~modified_ledger["entry_id"].isin(changed_entry_ids)
            ]
            modified_ledger = pd.concat(
                [modified_ledger, changed_rows],
                ignore_index=True,
            )

            for entry_id in changed_entry_ids:
                anomaly_type_by_entry[entry_id] = anomaly_name
                used_entry_ids.add(entry_id)

    modified_ledger = modified_ledger.sort_values(
        ["entry_id", "line_no"]
    ).reset_index(drop=True)

    label_rows = [
        {
            "entry_id": entry_id,
            "is_anomaly": entry_id in anomaly_type_by_entry,
            "anomaly_type": anomaly_type_by_entry.get(entry_id, ""),
        }
        for entry_id in modified_ledger["entry_id"].drop_duplicates()
    ]

    labels = pd.DataFrame(
        label_rows,
        columns=["entry_id", "is_anomaly", "anomaly_type"],
    )

    return modified_ledger, labels

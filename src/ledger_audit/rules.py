import pandas as pd
from math import log10

from ledger_audit.chart_of_accounts import accounts_of_type


def rule_self_approved(ledger: pd.DataFrame) -> pd.DataFrame:
    """Flag entries where the posting user is also the approver.

    Returns each matching entry ID once, even if the entry has multiple
    journal lines.
    """

    self_approved_mask = ledger["user_id"] == ledger["approver_id"]

    flagged_entry_ids = (
        ledger.loc[self_approved_mask, "entry_id"]
        .drop_duplicates()
        .tolist()
    )

    reason = "The posting user is also the approver."
    return pd.DataFrame({
        "entry_id": flagged_entry_ids,
        "reason": [reason] * len(flagged_entry_ids),
    })


def rule_odd_timing(ledger: pd.DataFrame) -> pd.DataFrame:
    """
    Flag entries posted on weekends or outside the usual hour range.

    Weekend entries are flagged at any hour. Weekday entries are flagged before
    6 a.m. or at or after 10 p.m.
    """

    weekend_mask = ledger["posted_at"].dt.weekday >= 5
    outside_hours_mask = (
        (ledger["posted_at"].dt.hour < 6)
        | (ledger["posted_at"].dt.hour >= 22)
    )

    flagged_mask = weekend_mask | outside_hours_mask

    flagged_entry_ids = (
        ledger.loc[flagged_mask, "entry_id"]
        .drop_duplicates()
        .tolist()
    )

    reason = "The entry was posted on a weekend or outside allowed hours."
    return pd.DataFrame({
        "entry_id": flagged_entry_ids,
        "reason": [reason] * len(flagged_entry_ids),
    })


def rule_duplicate(ledger: pd.DataFrame) -> pd.DataFrame:
    """
    Flag supplier payments matching another payment by vendor, amount, and date.

    A pair matches when the payments have the same vendor and total debit amount
    and were posted no more than five days apart. Both entries in a matching
    pair are returned.
    """

    payment_rows = ledger.loc[
        ledger["description"] == "Supplier payment"
    ]

    payment_entries = (
        payment_rows.groupby("entry_id", as_index=False)
        .agg(
            vendor_id=("vendor_id", "first"),
            posted_at=("posted_at", "first"),
            total_amount_pence=("debit_pence", "sum"),
        )
    )

    duplicate_entry_ids = set()

    for _, payment in payment_entries.iterrows():
        matching_mask = (
            (payment_entries["entry_id"] != payment["entry_id"])
            & (payment_entries["vendor_id"] == payment["vendor_id"])
            & (payment_entries["total_amount_pence"] == payment["total_amount_pence"])
            & (
                (payment_entries["posted_at"] - payment["posted_at"]).abs()
                <= pd.Timedelta(days=5)
            )
        )

        if matching_mask.any():
            duplicate_entry_ids.add(int(payment["entry_id"]))
            duplicate_entry_ids.update(
                payment_entries.loc[matching_mask,
                                    "entry_id"].astype(int).tolist()
            )

    flagged_entry_ids = sorted(duplicate_entry_ids)

    reason = "Another supplier payment has the same vendor and amount within five days."

    return pd.DataFrame({
        "entry_id": flagged_entry_ids,
        "reason": [reason] * len(flagged_entry_ids),
    })


def rule_below_limit(ledger: pd.DataFrame) -> pd.DataFrame:
    """Flag net expense amounts between £9,700 and £9,999.99 inclusive.

    Uses positive debit lines on chart-of-accounts expense accounts. VAT is
    excluded, so the checked amount is the net expense amount.
    """

    expense_account_codes = {
        account.code for account in accounts_of_type("expense")
    }

    expense_lines = ledger.loc[
        ledger["account_code"].isin(expense_account_codes)
        & (ledger["debit_pence"] > 0)
    ]

    expense_amounts = expense_lines.groupby("entry_id")["debit_pence"].sum()
    flagged_amounts = expense_amounts.loc[
        expense_amounts.between(970_000, 999_999)
    ]

    flagged_entry_ids = flagged_amounts.index.tolist()

    reason = "The net expense amount is just below the £10,000 approval limit."
    return pd.DataFrame({
        "entry_id": flagged_entry_ids,
        "reason": [reason] * len(flagged_entry_ids),
    })


def rule_round_number(ledger: pd.DataFrame) -> pd.DataFrame:
    """Flag entry amounts that are exact multiples of £100.

    For ordinary expenses, checks the net expense debit and excludes VAT.
    For other entries, checks the sum of debit lines.
    """

    entry_amounts = ledger.groupby("entry_id")["debit_pence"].sum()

    expense_rows = ledger.loc[
        (ledger["description"] == "Expense")
        & (ledger["account_code"] != 1200)
        & (ledger["debit_pence"] > 0)
    ]

    net_expense_amounts = expense_rows.groupby("entry_id")["debit_pence"].sum()

    entry_amounts.loc[net_expense_amounts.index] = net_expense_amounts

    flagged_amounts = entry_amounts.loc[
        entry_amounts % 10_000 == 0
    ]

    flagged_entry_ids = flagged_amounts.index.tolist()

    reason = "The entry amount is an exact multiple of £100."
    return pd.DataFrame({
        "entry_id": flagged_entry_ids,
        "reason": [reason] * len(flagged_entry_ids),
    })


def rule_benfords_law(ledger: pd.DataFrame) -> pd.DataFrame:
    """Flag entries whose largest line has a leading digit from an unusual bucket.

    Compares the dataset's leading-digit frequencies with Benford's expected
    frequencies. Flags entries whose digit belongs to a bucket with more than
    30% relative deviation. This is a population-level screening rule, not
    evidence that an individual entry is fraudulent.
    """

    line_amounts = ledger["debit_pence"].where(
        ledger["debit_pence"] > 0,
        ledger["credit_pence"],
    )

    line_amount_table = pd.DataFrame({
        "entry_id": ledger["entry_id"],
        "line_amount_pence": line_amounts,
    })

    largest_line_indices = (
        line_amount_table.groupby("entry_id")["line_amount_pence"].idxmax()
    )
    largest_lines = line_amount_table.loc[largest_line_indices]

    leading_digits = (
        largest_lines.set_index("entry_id")["line_amount_pence"]
        .astype(int)
        .astype(str)
        .str[0]
        .astype(int)
    )

    observed_frequencies = (
        leading_digits.value_counts(normalize=True)
        .reindex(range(1, 10), fill_value=0)
    )

    expected_frequencies = pd.Series({
        digit: log10(1 + 1 / digit)
        for digit in range(1, 10)
    })

    relative_deviations = (
        (observed_frequencies - expected_frequencies).abs()
        / expected_frequencies
    )
    unusual_digits = set(
        relative_deviations.loc[relative_deviations > 0.3].index
    )

    flagged_entry_ids = sorted(
        leading_digits.loc[leading_digits.isin(unusual_digits)].index.tolist()
    )

    reason = "The entry's leading digit belongs to a bucket deviating over 30% from Benford's expectation."
    return pd.DataFrame({
        "entry_id": flagged_entry_ids,
        "reason": [reason] * len(flagged_entry_ids),
    })


def run_all_rules(ledger: pd.DataFrame) -> pd.DataFrame:
    """Run every audit rule and combine their findings into one table.

    Adds a rule_name column to identify which rule flagged each entry. An entry
    may appear more than once if different rules flag it.
    """

    rule_functions = [
        ("benfords_law", rule_benfords_law),
        ("duplicate", rule_duplicate),
        ("below_limit", rule_below_limit),
        ("odd_timing", rule_odd_timing),
        ("self_approved", rule_self_approved),
        ("round_number", rule_round_number),
    ]

    rule_results = []

    for rule_name, rule_function in rule_functions:

        findings = rule_function(ledger).copy()
        findings["rule_name"] = rule_name
        rule_results.append(findings)

    combined_results = pd.concat(rule_results, ignore_index=True)

    return combined_results[["entry_id", "reason", "rule_name"]]

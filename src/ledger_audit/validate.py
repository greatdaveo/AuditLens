import pandas as pd


def unbalanced_entries(ledger: pd.DataFrame) -> pd.DataFrame:
    totals = (
        ledger.groupby("entry_id", as_index=False)[
            ["debit_pence", "credit_pence"]
        ]
        .sum()
    )
    return totals.loc[totals["debit_pence"] != totals["credit_pence"]]


def trial_balance(ledger: pd.DataFrame) -> pd.DataFrame:
    balances = (
        ledger.groupby("account_code", as_index=False)[
            ["debit_pence", "credit_pence"]
        ]
        .sum()
    )
    balances["balance_pence"] = (
        balances["debit_pence"] - balances["credit_pence"]
    )
    return balances

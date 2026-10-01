from dataclasses import dataclass


@dataclass
class Account:
    code: int
    name: str
    type: str


ACCOUNTS = [
    Account(1000, "Bank", "asset"),
    Account(1100, "Trade receivables", "asset"),
    Account(1200, "VAT recoverable", "asset"),
    Account(2000, "Trade payables", "liability"),
    Account(2100, "VAT payable", "liability"),
    Account(2200, "Accruals", "liability"),
    Account(3000, "Share capital", "equity"),
    Account(3100, "Retained earnings", "equity"),
    Account(4000, "Sales revenue", "revenue"),
    Account(6000, "Rent", "expense"),
    Account(6100, "Utilities", "expense"),
    Account(6200, "Software subscriptions", "expense"),
    Account(6300, "Professional fees", "expense"),
    Account(6400, "Travel", "expense"),
    Account(6500, "Depreciation", "expense"),
    Account(7000, "Wages", "expense"),
]


def accounts_of_type(account_type: str) -> list[Account]:
    result = []

    for account in ACCOUNTS:
        if account_type == account.type:
            result.append(account)
    return result

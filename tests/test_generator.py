import pandas as pd
import pytest

from ledger_audit.generator import USER_ROLES, generate_ledger
from ledger_audit.validate import trial_balance, unbalanced_entries


@pytest.fixture(scope="module")
def ledger():
    return generate_ledger(
        n_entries=2000,
        seed=42,
        start=pd.Timestamp("2024-01-01").to_pydatetime(),
        days=365,
    )


def test_every_entry_balances(ledger):
    assert unbalanced_entries(ledger).empty


def test_same_seed_gives_same_ledger(ledger):
    second_ledger = generate_ledger(
        n_entries=2000,
        seed=42,
        start=pd.Timestamp("2024-01-01").to_pydatetime(),
        days=365,
    )
    pd.testing.assert_frame_equal(ledger, second_ledger)


def test_user_never_approves_own_entry(ledger):
    assert (ledger["user_id"] != ledger["approver_id"]).all()


def test_no_weekend_postings(ledger):
    assert (ledger["posted_at"].dt.weekday < 5).all()


def test_postings_within_working_hours(ledger):
    assert ledger["posted_at"].dt.hour.between(9, 17).all()


def test_only_payroll_user_posts_payroll(ledger):
    payroll_user_ids = {
        user_id for user_id, role in USER_ROLES.items()
        if role == "payroll"
    }
    payroll_rows = ledger.loc[ledger["description"] == "Payroll"]
    assert not payroll_rows.empty
    assert set(payroll_rows["user_id"]) == payroll_user_ids


def test_trial_balance_nets_to_zero(ledger):
    assert trial_balance(ledger)["balance_pence"].sum() == 0

import pandas as pd
import pytest

from ledger_audit.features import build_entry_table, add_time_features, add_behaviour_features, build_feature_table
from ledger_audit.generator import generate_ledger


def test_build_entry_table_collapse_lines_into_new_row_per_entry():
    posted_at = pd.Timestamp("2024-01-08 10:30:00", tz="UTC")
    
    ledger = pd.DataFrame([
        {
            "entry_id": 10,
            "line_no": 1,
            "posted_at": posted_at,
            "account_code": 1100,
            "debit_pence": 50_000,
            "credit_pence": 0,
            "user_id": "U01",
            "approver_id": "A01",
            "customer_id": "C01",
            "vendor_id": "",
            "description": "Sale",
        },
        {
            "entry_id": 10,
            "line_no": 2,
            "posted_at": posted_at,
            "account_code": 4000,
            "debit_pence": 0,
            "credit_pence": 50_000,
            "user_id": "U01",
            "approver_id": "A01",
            "customer_id": "C01",
            "vendor_id": "",
            "description": "Sale",
        },
        {
            "entry_id": 11,
            "line_no": 1,
            "posted_at": posted_at,
            "account_code": 6300,
            "debit_pence": 60_000,
            "credit_pence": 0,
            "user_id": "U02",
            "approver_id": "A02",
            "customer_id": "",
            "vendor_id": "V02",
            "description": "Expense",
        },
        {
            "entry_id": 11,
            "line_no": 2,
            "posted_at": posted_at,
            "account_code": 1200,
            "debit_pence": 12_000,
            "credit_pence": 0,
            "user_id": "U02",
            "approver_id": "A02",
            "customer_id": "",
            "vendor_id": "V02",
            "description": "Expense",
        },
        {
            "entry_id": 11,
            "line_no": 3,
            "posted_at": posted_at,
            "account_code": 2000,
            "debit_pence": 0,
            "credit_pence": 72_000,
            "user_id": "U02",
            "approver_id": "A02",
            "customer_id": "",
            "vendor_id": "V02",
            "description": "Expense",
        },
    ])
    
    entries = build_entry_table(ledger)
    
    assert len(entries) == 2
    assert entries["entry_id"].is_unique
    
    sale = entries.loc[entries["entry_id"] == 10].iloc[0]
    assert sale["total_amount_pence"] == 50_000
    assert sale["n_lines"] == 2
    assert sale["account_codes"] == (1100, 4000)
    assert sale["customer_id"] == "C01"
    
    expense = entries.loc[entries["entry_id"] == 11].iloc[0]
    assert expense["total_amount_pence"] == 72_000
    assert expense["n_lines"] == 3  
    assert expense["account_codes"] == (1200, 2000, 6300)
    assert expense["vendor_id"] == "V02"


def test_add_time_features_extracts_hour_weekday_weekend_and_month_end():
    entries = pd.DataFrame({
        "entry_id": [1, 2, 3, 4],
        "posted_at": pd.to_datetime([
            "2024-01-08 10:30:00",  # Monday, mid-month
            "2024-01-13 23:15:00",  # Saturday night
            "2024-01-30 09:00:00",  # Tuesday, two days before month end
            "2024-01-29 09:00:00",  # Monday, three days before month end
        ], utc=True),
    })

    result = add_time_features(entries)

    assert result["hour"].tolist() == [10, 23, 9, 9]
    assert result["weekday"].tolist() == [0, 5, 1, 0]
    assert result["is_weekend"].tolist() == [False, True, False, False]
    assert result["is_month_end"].tolist() == [False, False, True, False]
    assert "hour" not in entries.columns  


def test_behaviour_features_use_only_past_data():
    entries = pd.DataFrame({
        "entry_id": [1, 2, 3, 4],
        "posted_at": pd.to_datetime([
            "2024-01-02 09:00:00",
            "2024-01-03 09:00:00",
            "2024-01-04 09:00:00",
            "2024-01-05 09:00:00",
        ], utc=True),
        "user_id": ["U01", "U01", "U01", "U01"],
        # The last amount is huge, it must not influence row 3.
        "total_amount_pence": [100, 200, 300, 10_000],       
        "account_codes": [(1100, 4000)] * 4,
        "vendor_id": [""] * 4,
    })

    result = add_behaviour_features(entries)

    # Row 3 sees past amounts 100 and 200: mean 150, sample std ~70.71.
    assert result["user_amount_zscore"].iloc[2] == pytest.approx(
        150 / (50 * 2 ** 0.5))
    # No history, or only one past amount (no spread), gives 0.
    assert result["user_amount_zscore"].iloc[0] == 0
    assert result["user_amount_zscore"].iloc[1] == 0


def _hour_entries():
    return pd.DataFrame({
        "entry_id": [1, 2, 3, 4, 5],
        "posted_at": pd.to_datetime([
            "2024-01-02 09:00:00",
            "2024-01-03 09:30:00",
            "2024-01-04 14:00:00",
            "2024-01-05 09:15:00",
            "2024-01-06 09:00:00",
        ], utc=True),
        "user_id": ["U01", "U01", "U01", "U01", "U02"],
        "total_amount_pence": [100, 200, 300, 400, 500],
        "account_codes": [(1100, 4000)] * 5,
        "vendor_id": [""] * 5,
    })


def test_first_entry_defaults():
    result = add_behaviour_features(_hour_entries())
    first_per_user = result.groupby("user_id").head(1)

    assert (first_per_user["user_amount_zscore"] == 0).all()
    assert (first_per_user["user_hour_typicality"] == 1.0).all()


def test_hour_typicality_uses_only_past_entries_at_same_hour():
    result = add_behaviour_features(_hour_entries())

    # U01 posts at hours 9, 9, 14, 9; each row sees only the hours before it.
    expected = [1.0, 1.0, 0.0, pytest.approx(2 / 3), 1.0]
    assert result["user_hour_typicality"].tolist() == expected
    
    
def test_days_since_similar_uses_same_user_and_account_set():
    entries = pd.DataFrame({
        "entry_id": [1, 2, 3, 4, 5],
        "posted_at": pd.to_datetime([
            "2024-01-02 09:00:00",
            "2024-01-03 09:00:00",
            "2024-01-05 09:00:00",
            "2024-01-10 09:00:00",
            "2024-01-11 09:00:00",
        ], utc=True),
        "user_id": ["U01", "U01", "U01", "U01", "U02"],
        "total_amount_pence": [100, 200, 300, 400, 500],
        "account_codes": [
            (1100, 4000),
            (1200, 2000, 6300),
            (1100, 4000),
            (1100, 4000),
            (1100, 4000),
        ],
        "vendor_id": [""] * 5,
    })

    result = add_behaviour_features(entries)

    # Rows 3 and 4 repeat U01's first account set after 3 and 5 days.
    # Row 5 uses the same set but belongs to U02, so it is a first occurrence.
    assert result["days_since_similar"].tolist() == [999, 999, 3, 5, 999]


def test_vendor_entry_count_so_far_counts_earlier_entries_per_vendor():
    entries = pd.DataFrame({
        "entry_id": [1, 2, 3, 4, 5, 6],
        "posted_at": pd.to_datetime([
            "2024-01-02 09:00:00",
            "2024-01-03 09:00:00",
            "2024-01-04 09:00:00",
            "2024-01-05 09:00:00",
            "2024-01-06 09:00:00",
            "2024-01-07 09:00:00",
        ], utc=True),
        "user_id": ["U01"] * 6,
        "total_amount_pence": [100, 200, 300, 400, 500, 600],
        "account_codes": [(1100, 4000)] * 6,
        "vendor_id": ["V01", "V01", "", "", "V02", "V01"],
    })

    result = add_behaviour_features(entries)

    # Blank vendors always count 0, however many blank entries came before.
    assert result["vendor_entry_count_so_far"].tolist() == [0, 1, 0, 0, 0, 2]


def _pipeline_entries():
    ledger = generate_ledger(
        n_entries=300,
        seed=1,
        start=pd.Timestamp("2024-01-01").to_pydatetime(),
        days=60,
    )
    entries = add_time_features(build_entry_table(ledger))
    return add_behaviour_features(entries)


def test_no_label_leakage():
    entries = _pipeline_entries()
    entries["is_anomaly"] = False
    entries["anomaly_type"] = ""

    features = build_feature_table(entries)

    assert "is_anomaly" not in features.columns
    assert "anomaly_type" not in features.columns


def test_feature_table_is_numeric_and_indexed_by_entry_id():
    features = build_feature_table(_pipeline_entries())

    assert features.index.name == "entry_id"
    assert features.index.is_unique
    assert not features.isna().any().any()
    assert all(pd.api.types.is_numeric_dtype(dtype)
               for dtype in features.dtypes)
    assert not any(dtype == bool for dtype in features.dtypes)

    # user_id and weekday are one-hot encoded with the first category dropped.
    assert "user_id" not in features.columns
    assert "user_id_U01" not in features.columns
    assert "user_id_U02" in features.columns

    one_hot = features.columns.str.startswith(("user_id_", "weekday_"))
    assert (~one_hot).sum() >= 10

import pandas as pd
import numpy as np


def build_entry_table(ledger: pd.DataFrame) -> pd.DataFrame:
    """Collapse journal lines into one row per entry."""
    
    return (
        ledger.groupby("entry_id", as_index=False)
        .agg(
            posted_at=("posted_at", "first"),
            user_id=("user_id", "first"),
            approver_id=("approver_id", "first"),
            total_amount_pence=("debit_pence", "sum"),
            n_lines=("line_no", "count"),
            account_codes=(
                "account_code", lambda codes: tuple(sorted(set(codes)))),
            customer_id=("customer_id", "first"),
            vendor_id=("vendor_id", "first"),
            description=("description", "first"),
        )
    )


def add_time_features(entries: pd.DataFrame) -> pd.DataFrame:
    """Add hour, weekday, weekend and month-end flags from posted_at."""
    
    result = entries.copy()
    posted_at = result["posted_at"]

    result["hour"] = posted_at.dt.hour
    result["weekday"] = posted_at.dt.weekday
    result["is_weekend"] = result["weekday"] >= 5
    result["is_month_end"] = posted_at.dt.day >= posted_at.dt.days_in_month - 1

    return result


def add_behaviour_features(entries: pd.DataFrame) -> pd.DataFrame:
    """Add features comparing each entry with the same user's earlier entries."""
    
    result = entries.sort_values(
        ["posted_at", "entry_id"]).reset_index(drop=True)
    amounts = result["total_amount_pence"].astype(float)
    by_user = amounts.groupby(result["user_id"])

    # shift(1) drops the current row, so only earlier entries are summarized
    past_mean = by_user.transform(lambda s: s.expanding().mean().shift(1))
    past_std = by_user.transform(lambda s: s.expanding().std().shift(1))

    zscore = (amounts - past_mean) / past_std
    result["user_amount_zscore"] = zscore.where(past_std > 0, 0.0)
    
    hours = result["posted_at"].dt.hour
    past_entries = result.groupby("user_id").cumcount()
    past_same_hour = result.groupby(["user_id", hours]).cumcount()

    typicality = past_same_hour / past_entries
    result["user_hour_typicality"] = typicality.where(past_entries > 0, 1.0)
    
    gap = result.groupby(["user_id", "account_codes"])["posted_at"].diff()
    result["days_since_similar"] = (gap.dt.total_seconds() / 86400).fillna(999)

    # Blank IDs read back from CSV are missing values, so treat both as blank.
    vendor_ids = result["vendor_id"].fillna("")
    vendor_count = result.groupby(vendor_ids).cumcount()
    result["vendor_entry_count_so_far"] = vendor_count.where(
        vendor_ids != "", 0)

    return result


def build_feature_table(entries: pd.DataFrame) -> pd.DataFrame:
    """Build the numeric model input, indexed by entry_id and free of label columns."""
    
    numeric_columns = [
        "total_amount_pence",
        "n_lines",
        "hour",
        "is_weekend",
        "is_month_end",
        "user_amount_zscore",
        "user_hour_typicality",
        "days_since_similar",
        "vendor_entry_count_so_far",
    ]

    # Columns are chosen by name, so anything else in entries (labels included) is dropped.
    features = entries[["entry_id", *numeric_columns]].set_index("entry_id")
    features[["is_weekend", "is_month_end"]] = features[[
        "is_weekend", "is_month_end"]].astype(int)
    features["log_amount"] = np.log1p(features["total_amount_pence"])

    one_hot = pd.get_dummies(
        entries[["entry_id", "user_id", "weekday"]].set_index("entry_id"),
        columns=["user_id", "weekday"],
        drop_first=True,
        dtype=int,
    )

    return pd.concat([features, one_hot], axis=1)

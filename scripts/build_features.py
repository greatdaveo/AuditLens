from pathlib import Path
import pandas as pd

from ledger_audit.features import (
    add_behaviour_features,
    add_time_features,
    build_entry_table,
    build_feature_table,
)


def main() -> None:
    """Build the feature table from the anomaly ledger and save it without labels."""
    
    ledger_path = Path("data/raw/ledger_v3_with_anomalies.csv")
    features_path = Path("data/processed/features.csv")

    ledger = pd.read_csv(ledger_path)
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)

    entries = build_entry_table(ledger)
    entries = add_time_features(entries)
    entries = add_behaviour_features(entries)
    features = build_feature_table(entries)

    assert "is_anomaly" not in features.columns and "anomaly_type" not in features.columns

    features.to_csv(features_path)

    print(f"Rows: {len(features)}")
    print(f"Columns: {features.shape[1]}")
    print(list(features.columns))


if __name__ == "__main__":
    main()

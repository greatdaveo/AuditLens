from pathlib import Path
import pandas as pd


from ledger_audit.anomalies import inject_all

from ledger_audit.validate import unbalanced_entries


RATES = {
    "duplicate_payment": 0.0015,
    "below_limit": 0.0015,
    "odd_timing": 0.0015,
    "self_approved": 0.001,
    "round_number": 0.0015,
    "rare_pairing": 0.001,
}


def main() -> None:
    input_path = Path("data/raw/ledger_v2.csv")
    ledger_output_path = Path("data/raw/ledger_v3_with_anomalies.csv")
    labels_output_path = Path("data/processed/labels.csv")

    ledger = pd.read_csv(input_path)
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)

    anomalous_ledger, labels = inject_all(
        ledger,
        seed=99,
        rates=RATES,
    )

    unbalanced = unbalanced_entries(anomalous_ledger)
    if not unbalanced.empty:
        raise ValueError(
            f"Anomaly injection created {len(unbalanced)} unbalanced entries")

    anomalous_ledger.to_csv(ledger_output_path, index=False)
    labels.to_csv(labels_output_path, index=False)

    counts = (
        labels.loc[labels["is_anomaly"]]
        .groupby("anomaly_type")
        .size()
        .rename("count")
        .to_frame()
    )
    counts["percentage"] = counts["count"] / len(labels) * 100
    print(counts.to_string())


if __name__ == "__main__":
    main()

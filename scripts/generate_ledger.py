from datetime import datetime
from pathlib import Path

from ledger_audit.generator import generate_ledger
from ledger_audit.validate import trial_balance, unbalanced_entries


def main() -> None:
    ledger = generate_ledger(
        n_entries=180_000,
        seed=42,
        start=datetime(2024, 1, 1),
        days=730,
    )

    output_path = Path("data/raw/ledger_v2.csv")
    ledger.to_csv(output_path, index=False)

    unbalanced = unbalanced_entries(ledger)

    print(f"Total lines: {len(ledger)}")
    print(f"Total entries: {ledger['entry_id'].nunique()}")
    print(f"Unbalanced count: {len(unbalanced)}")
    print(trial_balance(ledger).to_string(index=False))


if __name__ == "__main__":
    main()

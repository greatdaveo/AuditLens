from pathlib import Path
import pandas as pd

from ledger_audit.rules import run_all_rules


RULE_NAMES = [
    "benfords_law",
    "duplicate",
    "below_limit",
    "odd_timing",
    "self_approved",
    "round_number",
]

ANOMALY_TYPES = [
    "duplicate_payment",
    "below_limit",
    "odd_timing",
    "self_approved",
    "round_number",
    "rare_pairing",
]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format column headings and rows as a Markdown table."""

    table_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    table_lines.extend(
        "| " + " | ".join(row) + " |"
        for row in rows
    )

    return "\n".join(table_lines)


def main() -> None:
    """Run the audit rules, evaluate their findings, and write the results report."""

    ledger_path = Path("data/raw/ledger_v3_with_anomalies.csv")
    labels_path = Path("data/processed/labels.csv")
    results_path = Path("docs/results.md")

    ledger = pd.read_csv(ledger_path)
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)
    labels = pd.read_csv(labels_path)

    findings = run_all_rules(ledger)
    true_anomaly_ids = set(
        labels.loc[labels["is_anomaly"], "entry_id"]
    )

    precision_rows = []
    matrix_rows = []

    for rule_name in RULE_NAMES:
        predicted_ids = set(
            findings.loc[findings["rule_name"] == rule_name, "entry_id"]
        )
        true_positives = predicted_ids & true_anomaly_ids
        precision = len(true_positives) / \
            len(predicted_ids) if predicted_ids else 0.0
        recall = len(true_positives) / \
            len(true_anomaly_ids) if true_anomaly_ids else 0.0

        precision_rows.append([
            rule_name,
            f"{precision:.3f}",
            f"{recall:.3f}",
        ])

        type_counts = []

        for anomaly_type in ANOMALY_TYPES:
            type_entry_ids = set(
                labels.loc[labels["anomaly_type"] == anomaly_type, "entry_id"]
            )
            type_counts.append(
                str(len(predicted_ids & type_entry_ids))
            )

        matrix_rows.append([rule_name, *type_counts])

        print(f"{rule_name}: precision={precision:.3f}, recall={recall:.3f}")

    print("\nRule catches by anomaly type:")
    print(pd.DataFrame(
        matrix_rows,
        columns=["rule_name", *ANOMALY_TYPES],
    ).to_string(index=False))

    report_lines = [  # Builds the Markdown report contents.
        "# Rule performance",
        "",
        "Precision is the fraction of a rule's flags that are labelled anomalous. Recall is the fraction of labelled anomalies that the rule flags.",
        "",
        "## Precision and recall",
        "",
        markdown_table(  # Adds the metrics table.
            ["Rule", "Precision", "Recall"],
            precision_rows,
        ),
        "",
        "## Rule catches by anomaly type",
        "",
        "Each cell is the number of entries of that true anomaly type flagged by the rule.",
        "",
        markdown_table(  # Adds the six-by-six breakdown table.
            ["Rule", *ANOMALY_TYPES],
            matrix_rows,
        ),
        "",
    ]

    results_path.write_text("\n".join(report_lines), encoding="utf-8")


if __name__ == "__main__":
    main()

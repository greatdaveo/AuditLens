from pathlib import Path
import pandas as pd

from ledger_audit.evaluate import evaluate_model, error_breakdown
from ledger_audit.rules import (
    rule_self_approved,
    rule_odd_timing,
    rule_duplicate,
    rule_below_limit,
    rule_benfords_law,
    rule_round_number,
)


def main() -> None:
    """
    Evaluate all 6 rules + 4 models on the test split.
    Write results to docs/results.md.
    """

    ledger_path = Path("data/raw/ledger_v3_with_anomalies.csv")
    features_path = Path("data/processed/features.csv")
    labels_path = Path("data/processed/labels.csv")
    scores_path = Path("data/processed/scores.csv")
    models_dir = Path("data/processed/models")
    results_md = Path("docs/results.md")

    ledger = pd.read_csv(ledger_path)
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)

    # Read labels (includes both is_anomaly and anomaly_type columns)
    labels_full = pd.read_csv(labels_path, index_col="entry_id")
    labels = labels_full["is_anomaly"].astype(int)
    anomaly_types = labels_full["anomaly_type"]
    
    features = pd.read_csv(features_path, index_col="entry_id")
    scores_df = pd.read_csv(scores_path, index_col="entry_id")

    test_mask = scores_df["split"] == "test"
    test_ids = scores_df[test_mask].index

    y_test = labels.loc[test_ids]
    X_test = features.loc[test_ids]
    anomaly_types_test = anomaly_types.loc[test_ids]

    print(f"Test set: {len(test_ids)} entries, {y_test.sum()} anomalies")

    print("\nEvaluating rules...")
    ledger_test = ledger[ledger["entry_id"].isin(test_ids)]

    rule_methods = [
        ("Self-approved", rule_self_approved),
        ("Odd timing", rule_odd_timing),
        ("Duplicate", rule_duplicate),
        ("Below limit", rule_below_limit),
        ("Benford's law", rule_benfords_law),
        ("Round number", rule_round_number),
    ]

    rule_results = {}
    for rule_name, rule_func in rule_methods:
        # Run the rule on test ledger
        flagged_df = rule_func(ledger_test)
        flagged_ids = set(flagged_df["entry_id"].unique())

        # Create score array: 1 if flagged, 0 if not
        scores = pd.Series(0, index=test_ids)
        scores[scores.index.isin(flagged_ids)] = 1

        # Evaluate
        metrics = evaluate_model(y_test, scores)
        rule_results[rule_name] = metrics
        print(f"  {rule_name}: PR-AUC={metrics['pr_auc']:.4f}")

    # Create "any rule fired" score
    print("  Any rule...")
    any_rule_scores = pd.Series(0, index=test_ids)
    for rule_name, rule_func in rule_methods:
        flagged_df = rule_func(ledger_test)
        flagged_ids = set(flagged_df["entry_id"].unique())
        any_rule_scores[any_rule_scores.index.isin(flagged_ids)] = 1
    metrics = evaluate_model(y_test, any_rule_scores)
    rule_results["Any rule"] = metrics
    print(f"  Any rule: PR-AUC={metrics['pr_auc']:.4f}")

    # Evaluate each model
    print("\nEvaluating models...")
    model_names = ["logistic_score", "isolation_forest_score",
                   "xgboost_score", "autoencoder_score"]
    model_labels = ["Logistic Regression",
                    "Isolation Forest", "XGBoost", "Autoencoder"]

    model_results = {}
    for label, score_col in zip(model_labels, model_names):
        scores = scores_df.loc[test_ids, score_col]
        metrics = evaluate_model(y_test, scores)
        model_results[label] = metrics
        print(f"  {label}: PR-AUC={metrics['pr_auc']:.4f}")

    # Combine all results into a comparison table
    all_results = {**rule_results, **model_results}
    comparison_df = pd.DataFrame(all_results).T

    comparison_df = comparison_df.round(4)

    print("\nGenerating results table...")
    table_md = "## Results Comparison\n\n"
    table_md += comparison_df.to_markdown()
    table_md += "\n\n"

    # Generate per-type recall breakdown at k=500 for each method
    per_type_md = "## Per-Anomaly-Type Recall (top 500)\n\n"
    for method_name, method_scores in all_results.items():
        if method_name.startswith(("Logistic", "Isolation", "XGBoost", "Autoencoder")):
            # For models, use model scores
            score_col = None
            for label, col in zip(model_labels, model_names):
                if label == method_name:
                    score_col = col
                    break
            scores = scores_df.loc[test_ids, score_col]
        else:
            # For rules, recalculate
            if method_name == "Any rule":
                scores = any_rule_scores.values
            else:
                # Find matching rule
                for rule_name, rule_func in rule_methods:
                    if rule_name == method_name:
                        flagged_df = rule_func(ledger_test)
                        flagged_ids = set(flagged_df["entry_id"].unique())
                        scores = pd.Series(0, index=test_ids)
                        scores[scores.index.isin(flagged_ids)] = 1
                        break

        breakdown = error_breakdown(y_test, scores, anomaly_types_test, k=500)
        per_type_md += f"\n### {method_name}\n\n"
        per_type_md += breakdown.to_markdown(index=False)
        per_type_md += "\n"

    # Write results
    results_content = table_md + per_type_md
    results_content += """
                    ## Which method wins for which anomaly type, and why
                    """

    results_md.write_text(results_content)
    print(f"\nWrote results to {results_md}")


if __name__ == "__main__":
    main()

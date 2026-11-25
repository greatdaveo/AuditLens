import shap
import pandas as pd
from sklearn.metrics import average_precision_score



def evaluate_model(y_true, scores) -> dict:
    """
    Evaluate anomaly detection performance using standard metrics.

    y_true: (1 = anomaly, 0 = normal)
    scores: (higher = more anomalous)    
    """

    pr_auc = average_precision_score(y_true, scores)

    sorted_indices = pd.Series(scores).argsort()[::-1].values
    y_sorted = pd.Series(y_true).iloc[sorted_indices].values

    top_100 = y_sorted[:100]
    num_anomalies_in_top_100 = top_100.sum()
    precision_at_100 = num_anomalies_in_top_100 / len(top_100)

    total_anomalies = y_true.sum()
    recall_at_100 = num_anomalies_in_top_100 / total_anomalies

    top_500 = y_sorted[:500]
    num_anomalies_in_top_500 = top_500.sum()
    precision_at_500 = num_anomalies_in_top_500 / len(top_500)
    recall_at_500 = num_anomalies_in_top_500 / total_anomalies

    return {
        "pr_auc": pr_auc,
        "precision_at_100": precision_at_100,
        "recall_at_100": recall_at_100,
        "precision_at_500": precision_at_500,
        "recall_at_500": recall_at_500,
    }


def error_breakdown(y_true, scores, anomaly_type, k) -> pd.DataFrame:
    """
    For the top-k scored entries, break down how many anomalies of each type
    were caught vs. how many of each type exist in total.
    
    If there are 50 "duplicate" anomalies total in the dataset, but only 30 appear
    in the top 500 scored entries, then recall for "duplicate" at k=500 is 30/50 = 0.60.
    """

    scores_series = pd.Series(scores)
    y_true_series = pd.Series(y_true)

    sorted_indices = scores_series.argsort()[::-1].values
    top_k_indices = sorted_indices[:k]

    caught_data = []
    for idx in top_k_indices:
        if y_true_series.iloc[idx] == 1: 
            caught_data.append(anomaly_type.iloc[idx])

    caught_counts = pd.Series(caught_data).value_counts()

    mask_anomalies = y_true_series == 1
    total_counts = anomaly_type[mask_anomalies].value_counts()

    all_types = sorted(set(caught_counts.index) | set(total_counts.index))
    results = []
    for atype in all_types:
        caught = caught_counts.get(atype, 0)
        total = total_counts.get(atype, 0)
        recall = caught / total if total > 0 else 0
        results.append({
            "anomaly_type": atype,
            "caught_in_top_k": caught,
            "total_in_dataset": total,
            "recall": recall,
        })

    return pd.DataFrame(results)


def explain_xgboost(model, X, entry_ids, top_n=5) -> pd.DataFrame:
    """Explain XGBoost predictions using SHAP values."""

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    reasons = []

    for idx, entry_id in enumerate(entry_ids):
        shap_abs = pd.Series(shap_values[idx]).abs()
        top_indices = shap_abs.nlargest(top_n).index.tolist()

        feature_explanations = []
        for feature_idx in top_indices:
            feature_name = X.columns[feature_idx]
            feature_value = X.iloc[idx, feature_idx]
            shap_value = shap_values[idx, feature_idx]

            direction = "higher" if shap_value > 0 else "lower"
            impact = abs(shap_value)

            explanation = f"{feature_name}={feature_value:.1f} ({direction} than typical, impact={impact:.3f})"
            feature_explanations.append(explanation)

        combined_reason = "; ".join(feature_explanations)
        reasons.append({
            "entry_id": entry_id,
            "shap_reason": combined_reason,
        })

    return pd.DataFrame(reasons)


def combine_reasons(rule_reasons: pd.DataFrame, shap_reasons: pd.DataFrame) -> pd.DataFrame:
    """ Combine rule-based reasons with SHAP-based reasons into one "why_flagged" field."""

    combined = rule_reasons.merge(shap_reasons, on="entry_id", how="outer")

    explanations = []
    for _, row in combined.iterrows():
        parts = []

        if pd.notna(row.get("reason")):
            parts.append(f"Rule: {row['reason']}")

        if pd.notna(row.get("shap_reason")):
            parts.append(f"Model: {row['shap_reason']}")

        why_flagged = " ".join(parts) if parts else "Unknown reason"

        explanations.append({
            "entry_id": row["entry_id"],
            "why_flagged": why_flagged,
        })

    return pd.DataFrame(explanations)

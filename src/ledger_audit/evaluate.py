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

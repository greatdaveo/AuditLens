from pathlib import Path

import joblib
import pandas as pd
import torch

from ledger_audit.models import (
    anomaly_scores,
    time_split,
    train_autoencoder,
    train_isolation_forest,
    train_logistic_regression,
    train_xgboost,
)


def main() -> None:
    """Train the four models on the training split and score every entry."""
    
    ledger_path = Path("data/raw/ledger_v3_with_anomalies.csv")
    features_path = Path("data/processed/features.csv")
    labels_path = Path("data/processed/labels.csv")
    models_dir = Path("data/processed/models")
    scores_path = Path("data/processed/scores.csv")
    models_dir.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(ledger_path, usecols=["entry_id", "posted_at"])
    ledger["posted_at"] = pd.to_datetime(ledger["posted_at"], utc=True)
    entries = ledger.groupby("entry_id", as_index=False)["posted_at"].first()

    features = pd.read_csv(features_path, index_col="entry_id")
    labels = pd.read_csv(labels_path, index_col="entry_id")[
        "is_anomaly"].astype(int)
    labels = labels.loc[features.index]

    train_ids, val_ids, test_ids = time_split(entries)
    for name, ids in [("train", train_ids), ("val", val_ids), ("test", test_ids)]:
        print(f"{name}: {len(ids)} entries, {labels.loc[ids].sum()} anomalies")

    X_train = features.loc[train_ids]
    y_train = labels.loc[train_ids]

    print("Training logistic regression...")
    logistic = train_logistic_regression(X_train, y_train)
    print("Training isolation forest...")
    isolation_forest = train_isolation_forest(X_train)
    print("Training XGBoost...")
    xgboost = train_xgboost(X_train, y_train)
    print("Training autoencoder...")
    autoencoder = train_autoencoder(X_train, y_train)

    joblib.dump(logistic, models_dir / "logistic_regression.joblib")
    joblib.dump(isolation_forest, models_dir / "isolation_forest.joblib")
    joblib.dump(xgboost, models_dir / "xgboost.joblib")
    # Loading this file later needs torch.load(path, weights_only=False).
    torch.save(autoencoder, models_dir / "autoencoder.pt")

    scores = pd.DataFrame(index=features.index)
    scores["logistic_score"] = anomaly_scores(logistic, features)
    scores["isolation_forest_score"] = anomaly_scores(
        isolation_forest, features)
    scores["xgboost_score"] = anomaly_scores(xgboost, features)
    scores["autoencoder_score"] = anomaly_scores(autoencoder, features)

    split = pd.Series("test", index=features.index)
    split.loc[train_ids] = "train"
    split.loc[val_ids] = "val"
    scores["split"] = split

    scores.to_csv(scores_path)
    print(f"Saved {len(scores)} scores to {scores_path}")


if __name__ == "__main__":
    main()

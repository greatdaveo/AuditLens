import numpy as np
import pandas as pd
import pytest

from ledger_audit.models import anomaly_scores, time_split, train_autoencoder, train_isolation_forest, train_logistic_regression, train_xgboost


def test_time_split_is_ordered_and_uses_the_timestamp_range():
    days = [0, 1, 2, 3, 4, 5, 6, 7, 50, 80, 90, 100]
    start = pd.Timestamp("2024-01-01", tz="UTC")
    entries = pd.DataFrame({
        "entry_id": range(1, 13),
        "posted_at": [start + pd.Timedelta(days=d) for d in days],
    })

    # Input order must not matter.
    train_ids, val_ids, test_ids = time_split(entries.iloc[::-1])

    posted_at = entries.set_index("entry_id")["posted_at"]
    assert posted_at.loc[train_ids].max() <= posted_at.loc[val_ids].min()
    assert posted_at.loc[val_ids].max() <= posted_at.loc[test_ids].min()

    # Boundaries sit at 70% and 85% of the 100-day range, not of the row count.
    assert sorted(train_ids) == list(range(1, 10))
    assert sorted(val_ids) == [10]
    assert sorted(test_ids) == [11, 12]


def test_logistic_regression_scores_anomalies_higher():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({
        "signal": rng.normal(size=500),
        "large_scale_noise": rng.normal(size=500) * 1e9,
    })
    y = (X["signal"] > 1.5).astype(int)

    model = train_logistic_regression(X, y)
    scores = anomaly_scores(model, X)

    labels = y.to_numpy()
    assert len(scores) == len(X)
    assert ((scores >= 0) & (scores <= 1)).all()
    assert scores[labels == 1].mean() > scores[labels == 0].mean()


def test_isolation_forest_scores_far_outliers_higher():
    rng = np.random.default_rng(1)
    inliers = rng.normal(size=(500, 2))
    outliers = np.array([[10, 10], [-10, 10], [10, -10], [-10, -10], [12, 0]])
    X = pd.DataFrame(np.vstack([inliers, outliers]), columns=["a", "b"])

    model = train_isolation_forest(X)
    scores = anomaly_scores(model, X)

    assert len(scores) == len(X)
    # The last five rows are the outliers, far beyond the normal cloud.
    assert scores[500:].min() > np.percentile(scores[:500], 99)


def test_xgboost_scores_anomalies_higher_and_weights_the_rare_class():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({
        "signal": rng.normal(size=500),
        "noise": rng.normal(size=500),
    })
    y = (X["signal"] > 1.5).astype(int)

    model = train_xgboost(X, y)
    scores = anomaly_scores(model, X)

    labels = y.to_numpy()
    expected_weight = (labels == 0).sum() / (labels == 1).sum()
    assert model.get_params()["scale_pos_weight"] == pytest.approx(
        expected_weight)
    assert ((scores >= 0) & (scores <= 1)).all()
    assert scores[labels == 1].mean() > scores[labels == 0].mean()


def _small_labelled_data():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({
        "a": rng.normal(size=300),
        "b": rng.normal(size=300),
        "c": rng.normal(size=300),
    })
    y = pd.Series([1 if i % 20 == 0 else 0 for i in range(300)])
    X.loc[y == 1] += 8  # Anomalies sit far from the normal rows.
    return X, y


def test_autoencoder_trained_only_on_normal():
    X, y = _small_labelled_data()

    model = train_autoencoder(X, y)

    assert model.n_training_rows == (y == 0).sum()


def test_autoencoder_scores_unusual_rows_higher():
    X, y = _small_labelled_data()

    model = train_autoencoder(X, y)
    scores = anomaly_scores(model, X)

    labels = y.to_numpy()
    assert scores[labels == 1].mean() > scores[labels == 0].mean()


def test_all_models_produce_scores_for_every_row():
    X, y = _small_labelled_data()
    models = [
        train_logistic_regression(X, y),
        train_isolation_forest(X),
        train_xgboost(X, y),
        train_autoencoder(X, y),
    ]

    for model in models:
        scores = anomaly_scores(model, X)
        assert len(scores) == len(X)
        assert not np.isnan(scores).any()

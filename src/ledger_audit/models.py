import pandas as pd
import torch
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from xgboost import XGBClassifier


def time_split(entries: pd.DataFrame) -> tuple[pd.Index, pd.Index, pd.Index]:
    """Split entry IDs into train, validation and test sets at 70% and 85% of the time range."""
    
    start = entries["posted_at"].min()
    end = entries["posted_at"].max()
    train_end = start + 0.70 * (end - start)
    val_end = start + 0.85 * (end - start)

    ordered = entries.sort_values(["posted_at", "entry_id"])
    posted_at = ordered["posted_at"]
    entry_ids = ordered["entry_id"]

    train_ids = pd.Index(entry_ids[posted_at < train_end])
    val_ids = pd.Index(
        entry_ids[(posted_at >= train_end) & (posted_at < val_end)])
    test_ids = pd.Index(entry_ids[posted_at >= val_end])

    return train_ids, val_ids, test_ids


def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series):
    """Fit a class-balanced logistic regression on standardised features."""
    
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=1000),
    )
    model.fit(X_train, y_train)
    return model


def train_isolation_forest(X_train: pd.DataFrame):
    """Fit an unsupervised isolation forest; labels are not used."""
    model = IsolationForest(
        n_estimators=200, contamination=0.01, random_state=42)
    model.fit(X_train)
    return model


def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series):
    """Fit gradient-boosted trees, weighting the rare anomaly class by the class ratio."""
    n_normal = int((y_train == 0).sum())
    n_anomaly = int((y_train == 1).sum())

    model = XGBClassifier(
        scale_pos_weight=n_normal / n_anomaly,
        max_depth=5,
        n_estimators=300,
        eval_metric="aucpr",
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


class Autoencoder(nn.Module):
    """Squeeze each row down to 8 numbers, then rebuild it."""

    def __init__(self, input_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 8),
            nn.ReLU(),
            nn.Linear(8, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x):
        return self.network(x)


def train_autoencoder(X_train: pd.DataFrame, y_train: pd.Series):
    """Train an autoencoder on the normal training rows only."""
    
    normal_rows = X_train[y_train.to_numpy() == 0]
    scaler = StandardScaler().fit(normal_rows)
    data = torch.tensor(scaler.transform(normal_rows), dtype=torch.float32)

    torch.manual_seed(42)
    model = Autoencoder(data.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_function = nn.MSELoss()
    loader = DataLoader(TensorDataset(data), batch_size=64, shuffle=True)

    for _ in range(50):
        for (batch,) in loader:
            optimizer.zero_grad()
            loss = loss_function(model(batch), batch)
            loss.backward()
            optimizer.step()

    model.eval()
    model.scaler = scaler
    model.n_training_rows = len(normal_rows)
    return model


def anomaly_scores(model, X: pd.DataFrame):
    """Return one anomaly score per row; higher means more anomalous."""
    
    if isinstance(model, IsolationForest):
        return -model.score_samples(X)
    if isinstance(model, nn.Module):
        data = torch.tensor(model.scaler.transform(X), dtype=torch.float32)
        with torch.no_grad():
            reconstruction = model(data)
        return ((reconstruction - data) ** 2).mean(dim=1).numpy()
    return model.predict_proba(X)[:, 1]

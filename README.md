# AuditLens: Anomaly Detection for Financial Ledgers

## Problem Statement

Financial audits rely on manual testing to catch fraud and errors in ledger entries. Rule-based audit procedures (e.g., "flag expenses above £10,000") are:
- **Slow**: Auditors manually review thousands of entries
- **Rigid**: New fraud patterns require writing new rules
- **Reactive**: They catch known patterns, not novel schemes

**AuditLens** combines rule-based detection with machine learning to automatically flag suspicious ledger entries, enabling auditors to focus on high-risk items.

---

## Approach

AuditLens uses a **hybrid detection model** combining domain expertise with machine learning:

1. **Synthetic data generation** (Stages 1–4): Create realistic journal entries with known fraud patterns injected at calibrated rates
2. **Rule-based audit tests** (Stage 6): Encode domain rules (e.g., "odd timing," "duplicate payments," "below-limit structuring")
3. **Feature engineering** (Stage 7): Build 20+ features capturing accounting patterns, user behavior, and temporal anomalies
4. **Machine learning models** (Stage 8): Train 4 models—Logistic Regression, Isolation Forest, XGBoost, and Autoencoder—to detect patterns beyond rules
5. **Evaluation** (Stage 9): Compare methods on PR-AUC, precision@k, and recall@k; break down performance by fraud type
6. **Explainability** (Stage 10): Use SHAP to explain why entries are flagged (which features drove the decision)

---

## Results

| Method | PR-AUC | Precision@100 | Recall@100 | Precision@500 | Recall@500 |
|--------|--------|---------------|------------|---------------|------------|
| Self-approved | 0.1079 | 0.23 | 0.1050 | 0.054 | 0.1233 |
| Odd timing | 0.2302 | 0.50 | 0.2283 | 0.106 | 0.2420 |
| Duplicate | 0.0869 | 0.36 | 0.1644 | 0.076 | 0.1735 |
| Below limit | 0.1326 | 0.41 | 0.1872 | 0.086 | 0.1963 |
| Benford's law | 0.0083 | 0.02 | 0.0091 | 0.010 | 0.0228 |
| Round number | 0.1341 | 0.51 | 0.2329 | 0.110 | 0.2511 |
| **Any rule (combined)** | **0.5515** | **0.69** | **0.3151** | **0.368** | **0.8402** |
| Logistic Regression | 0.2576 | 0.51 | 0.2329 | 0.110 | 0.2511 |
| Isolation Forest | 0.0143 | 0.00 | 0.0000 | 0.010 | 0.0228 |
| XGBoost | 0.3340 | 0.61 | 0.2785 | 0.186 | 0.4247 |
| Autoencoder | 0.1082 | 0.25 | 0.1142 | 0.118 | 0.2694 |

**Key finding**: Combining all 6 rules (PR-AUC=0.5515) outperforms individual methods and ML models, catching 84% of anomalies in the top 500 entries while maintaining 36.8% precision. XGBoost (PR-AUC=0.334) is the best ML model but lags the combined rules, suggesting domain knowledge encoded in rules is crucial for detecting specific fraud patterns.

---

## Limitations

**These results reflect detection of planted synthetic anomalies only**, not proven real-world fraud detection.

- **Synthetic data**: All anomalies were artificially injected following predefined rules. Real fraud is more diverse and may not match our patterns.
- **Class imbalance**: The dataset contains far more normal entries (26,176) than anomalies (219, 0.83%). Metrics like precision and recall depend heavily on threshold choice.
- **Fixed thresholds**: The approval limit (£10,000), Benford threshold (30% deviation), and other parameters were arbitrary design choices, not empirically derived from a real control environment.
- **No external validation**: The models and rules have not been tested on real-world ledgers or validated by domain experts.

Any production deployment would require validation on real data before use.

---

## Setup

### Requirements
- Python 3.9+
- pip

### Install

```bash
# Clone the repository
git clone https://github.com/greatdaveo/AuditLens.git
cd AuditLens

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package and dependencies
pip install -e .
```

### Run the Full Pipeline

To generate data, train models, and evaluate all methods:

```bash
# 1. Generate a synthetic ledger with realistic patterns
python scripts/generate_ledger.py

# 2. Inject known anomalies (6 types at calibrated rates)
python scripts/inject_anomalies.py

# 3. Build 20+ features capturing accounting and behavioral patterns
python scripts/build_features.py

# 4. Run rule-based audit tests (6 audit rules)
python scripts/run_rules.py

# 5. Train 4 machine learning models
python scripts/train_models.py

# 6. Evaluate all methods on the test set and generate results
python scripts/evaluate_all.py
```

Results are written to `docs/results.md` with a comparison table, per-anomaly-type breakdown, and professional analysis.

### Explore Results

View the top 20 most suspicious entries with human-readable explanations:

```bash
jupyter notebook notebooks/02_results.ipynb
```

This notebook shows each flagged entry's score, ground truth anomaly type, and a combined explanation of why it was flagged (from both audit rules and XGBoost's feature importance via SHAP).

### Run Tests

Verify everything works:

```bash
pytest -v
```

Tests run automatically on every push via GitHub Actions (see `.github/workflows/tests.yml`).

---

## Citation
This is a learning project demonstrating hybrid anomaly detection (rule-based + ML).

If you use this project, please cite:

```bibtex
@software{auditlens2026,
  title={AuditLens: Anomaly Detection for Financial Ledgers},
  author={David Olowomeye},
  year={2026},
  url={https://github.com/greatdaveo/AuditLens}
}
```

---

## Authors

**[David Olowomeye](https://github.com/greatdaveo)**

---

## Acknowledgments

- Bakumenko & Elragal (2022): "Detecting Anomalies in Financial Transactions"
- Schreyer et al. (2017, 2019): "Graph-based Fraud Detection"
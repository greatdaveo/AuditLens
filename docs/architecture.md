# AuditLens Architecture

## System Overview

AuditLens is a hybrid anomaly detection system that combines rule-based audit logic with machine learning to flag suspicious financial ledger entries. The system processes raw journal entries through feature engineering and detection models, then explains its decisions for auditor review.

---

## Processing Pipeline

**Stage 1–3: Ledger Generation**
- Define chart of accounts with account codes, names, and types (asset, liability, equity, revenue, expense)
- Generate synthetic journal entries with realistic patterns: posting users, approval workflows, amounts, dates
- Validate double-entry bookkeeping (debits = credits for each entry)
- Output: `ledger_v2.csv` (100,000 clean entries)

**Stage 4: Anomaly Injection**
- Inject 6 known fraud/error patterns at calibrated rates:
  - Self-approved payments (1 in 1000)
  - Duplicate transactions (1.5 in 1000)
  - Odd timing: weekends or outside 6 AM–10 PM (1.5 in 1000)
  - Below-limit structuring: £9,700–£9,999.99 (1.5 in 1000)
  - Round numbers: exact multiples of £100 (1.5 in 1000)
  - Rare account pairings (1 in 1000)
- Track which entries received which anomalies for ground truth labeling
- Split into 70% train, 15% validation, 15% test (by time)
- Output: `ledger_v3_with_anomalies.csv` (219 anomalies, 26,176 normal entries in test set)

**Stage 5: Feature Engineering (Stage 7)**
- Extract 20+ features per entry capturing:
  - **Account patterns**: Debit/credit amounts, account type, transaction frequency
  - **User behavior**: User's historical posting count, approval patterns, typical amounts
  - **Temporal patterns**: Day of week, hour of day, approval delay
  - **Transaction patterns**: Amount roundness, Benford's law first digit, duplicate signatures
- Normalize all features to 0–1 range
- Output: `features.csv` (20+ columns, one row per entry)

**Stage 6: Rule-Based Detection**
- Encode 6 audit rules as domain logic:
  - Rule: Self-approved (user = approver)
  - Rule: Odd timing (weekend or outside 6–22)
  - Rule: Duplicate (same vendor, amount, date within 5 days)
  - Rule: Below limit (£9,700–£9,999.99)
  - Rule: Benford (leading digit >30% deviation from expected)
  - Rule: Round number (multiples of £100)
- For each entry, determine which rules fire (if any)
- Output: Flagged entries with rule names and reasons

**Stage 7–8: Machine Learning Models**
- Train 4 models on training split using features:
  - **Logistic Regression**: Linear classifier with L2 regularization
  - **Isolation Forest**: Unsupervised anomaly detection (contamination=1%)
  - **XGBoost**: Gradient-boosted trees (100 trees, max depth 6)
  - **Autoencoder**: Neural network (32-8-32 architecture, 50 epochs, ReLU activation)
- Score every entry (0–1 probability of anomaly) using all models
- Output: `scores.csv` (one row per entry, columns for each model's score)

**Stage 9: Evaluation & Comparison**
- Evaluate each method on test set:
  - Rules individually (6 methods)
  - Rules combined as "any rule fired"
  - Each ML model (4 methods)
- Metrics: PR-AUC (overall quality), Precision@100 (top 100), Recall@100, Precision@500, Recall@500
- Break down performance by anomaly type (which methods catch which patterns best?)
- Output: Results table and per-type recall breakdown to `docs/results.md`

**Stage 10: Explainability**
- Use SHAP (SHapley Additive exPlanations) to explain XGBoost's decisions:
  - Calculate which features most influenced each prediction
  - Translate to human-readable format: "amount=£9,500 (higher than typical, impact=+0.23)"
- Merge rule-based reasons with SHAP reasons for each flagged entry
- Output: Top 20 entries in `notebooks/02_results.ipynb` with `why_flagged` field

---

## Data Flow

```
INPUT: Raw Ledger
       ↓
    [Stages 1–3]
    Generate Ledger
       ↓
OUTPUT: Synthetic ledger (100K entries)
       ↓
    [Stage 4]
    Inject Anomalies
       ↓
OUTPUT: Labeled ledger (219 anomalies)
       ↓
    [Split by time]
    Train (70%) | Val (15%) | Test (15%)
       ↓
    [Stage 7]
    Feature Engineering
       ↓
OUTPUT: Feature matrix (20+ columns)
       ├─ Routes to Rules (Stage 6)
       └─ Routes to Models (Stage 8)
       ↓
    [Rules]              [Models]
    6 audit rules        4 ML models
       ↓                     ↓
    Rule scores          Model scores
       ↓                     ↓
    └─────────┬──────────┘
              ↓
        [Stage 9]
        Evaluation
              ↓
OUTPUT: `docs/results.md`
  - Comparison table
  - Per-type breakdown
  - Analysis
              ↓
        [Stage 10]
        Explainability (SHAP)
              ↓
OUTPUT: `02_results.ipynb`
  - Top 20 entries
  - why_flagged reasons
  - Auditor-ready report
```

---

## Component Responsibilities

### Core Modules

**`chart_of_accounts.py`**
- Defines the chart of accounts (16 accounts with codes, names, types)
- Provides lookup: `accounts_of_type("expense")` → list of expense accounts
- Used by: generator, rules, features

**`generator.py`**
- Generates realistic synthetic entries with posting users, approval workflows, vendors, customers
- Implements 100K entries with 70 days of data, working hours, UK-based patterns
- Used by: Stage 1 script

**`validate.py`**
- Checks double-entry accounting (sum of debits = sum of credits per entry)
- Used by: Stages 1 and 4 to validate generated and anomalous data

**`anomalies.py`**
- Injects 6 anomaly types at specified rates
- Tracks which entries were modified and what anomalies were added
- Returns: modified ledger + labels DataFrame with `is_anomaly` and `anomaly_type`
- Used by: Stage 4 script

**`rules.py`**
- Implements 6 audit rules as functions
- Each rule returns a DataFrame: entry_id, reason, rule_name
- Functions: `rule_self_approved()`, `rule_odd_timing()`, `rule_duplicate()`, `rule_below_limit()`, `rule_benfords_law()`, `rule_round_number()`, `run_all_rules()`
- Used by: Stage 6 script and Stage 9 evaluation

**`features.py`**
- Builds 20+ features from ledger and labels
- Features grouped by: account patterns, user behavior, temporal, transaction signatures
- Output: DataFrame with entry_id as index, feature columns
- Used by: Stage 7 script

**`models.py`**
- Trains 4 models: Logistic Regression, Isolation Forest, XGBoost, Autoencoder
- Functions: `train_logistic_regression()`, `train_isolation_forest()`, `train_xgboost()`, `train_autoencoder()`
- Also provides: `time_split()` (70/15/15), `anomaly_scores()` (convert predictions to 0–1 scores)
- Used by: Stage 8 script

**`evaluate.py`**
- Evaluation metrics: `evaluate_model()` (PR-AUC, precision@k, recall@k)
- Error analysis: `error_breakdown()` (per-anomaly-type recall)
- Explainability: `explain_xgboost()` (SHAP), `combine_reasons()` (merge rule + SHAP)
- Used by: Stages 9–10

---

## Key Design Decisions

**Why Synthetic Data?**
- Real fraud data is rare, proprietary, and hard to obtain
- Synthetic data allows us to control anomaly rates and validate ground truth
- Limitation: Real fraud is more creative and may not match our patterns

**Why Hybrid Detection (Rules + ML)?**
- Rules encode domain knowledge (auditors know what suspicious looks like)
- ML detects patterns beyond explicit rules
- Combining both: rules catch known patterns precisely; ML catches novel ones
- Result: "Any rule" (PR-AUC=0.5515) beats individual ML models

**Why These 6 Rules?**
- Represent common audit procedures: approval controls, timing, deduplication, limits, Benford, round numbers
- Injected at rates reflecting typical audit sampling (0.1–0.15% anomalies)
- Each rule is independently verifiable (auditors can check the logic)

**Why These 4 Models?**
- Logistic Regression: Baseline linear model
- Isolation Forest: Unsupervised, works for rare events
- XGBoost: State-of-the-art supervised learner
- Autoencoder: Unsupervised deep learning, learns "normal" patterns

**Why PR-AUC, Not Accuracy?**
- Accuracy is misleading with class imbalance (99% normal, 1% anomaly)
- PR-AUC focuses on the minority class (anomalies), which auditors care about
- Precision@k answers: "Of the top k I investigate, how many are real?"
- Recall@k answers: "Of all anomalies, how many appear in my top k?"

---

## Deployment Path (Future)

**Current State (v1.0):**
- Synthetic data, proven detection logic, explainable decisions
- Ready for: learning, validation on real data, proof-of-concept pilots

**Stage 12 (SageMaker):**
- Migrate to AWS for scalability
- Retrain on real ledgers once available
- Deploy as real-time scoring endpoint

**Stage 13 (Application):**
- FastAPI backend for scoring
- Streamlit UI for auditor review
- Feedback loop: use audit approvals/rejections to improve models

**Stage 14 (Graph Version):**
- Add network analysis (accounts, users, vendors as graph nodes)
- Detect circular payments, round-tripping, money laundering patterns
- Compare graph-based vs. tabular detection

**Stage 15 (Research Paper):**
- Publish to arXiv: "When does structural fraud detection outperform tabular anomaly detection?"
- Central question: graph methods vs. tabular methods for which patterns?

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Data processing** | pandas, NumPy |
| **ML models** | scikit-learn, XGBoost, PyTorch |
| **Explainability** | SHAP |
| **Testing** | pytest |
| **Notebooks** | Jupyter |
| **CI/CD** | GitHub Actions |
| **Package management** | setuptools, pip |
| **Language** | Python 3.9+ |

---

## Running Each Stage

```bash
# Stage 1–3: Generate
python scripts/generate_ledger.py

# Stage 4: Inject anomalies
python scripts/inject_anomalies.py

# Stage 7: Features
python scripts/build_features.py

# Stage 6: Rules
python scripts/run_rules.py

# Stage 8: Models
python scripts/train_models.py

# Stage 9: Evaluate
python scripts/evaluate_all.py

# Stage 10: Explore
jupyter notebook notebooks/02_results.ipynb
```

Each script reads outputs from previous stages and writes outputs for the next stage.

---

## Testing

Run the test suite:

```bash
pytest -v
```

Tests cover:
- Ledger generation and validation
- Anomaly injection correctness
- Feature engineering consistency
- Rule logic
- Model training and scoring

GitHub Actions runs tests automatically on every push to `main` and all stage branches.

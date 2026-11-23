## Results Comparison

|                     |   pr_auc |   precision_at_100 |   recall_at_100 |   precision_at_500 |   recall_at_500 |
|:--------------------|---------:|-------------------:|----------------:|-------------------:|----------------:|
| Self-approved       |   0.1079 |               0.23 |          0.105  |              0.054 |          0.1233 |
| Odd timing          |   0.2302 |               0.5  |          0.2283 |              0.106 |          0.242  |
| Duplicate           |   0.0869 |               0.36 |          0.1644 |              0.076 |          0.1735 |
| Below limit         |   0.1326 |               0.41 |          0.1872 |              0.086 |          0.1963 |
| Benford's law       |   0.0083 |               0.02 |          0.0091 |              0.01  |          0.0228 |
| Round number        |   0.1341 |               0.51 |          0.2329 |              0.11  |          0.2511 |
| Any rule            |   0.5515 |               0.69 |          0.3151 |              0.368 |          0.8402 |
| Logistic Regression |   0.2576 |               0.51 |          0.2329 |              0.11  |          0.2511 |
| Isolation Forest    |   0.0143 |               0    |          0      |              0.01  |          0.0228 |
| XGBoost             |   0.334  |               0.61 |          0.2785 |              0.186 |          0.4247 |
| Autoencoder         |   0.1082 |               0.25 |          0.1142 |              0.118 |          0.2694 |

## Per-Anomaly-Type Recall (top 500)


### Self-approved

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 1 |                 41 | 0.0243902 |
| duplicate_payment |                 2 |                 36 | 0.0555556 |
| odd_timing        |                 0 |                 35 | 0         |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                 1 |                 51 | 0.0196078 |
| self_approved     |                22 |                 22 | 1         |

### Odd timing

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 1 |                 41 | 0.0243902 |
| duplicate_payment |                15 |                 36 | 0.416667  |
| odd_timing        |                35 |                 35 | 1         |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                 1 |                 51 | 0.0196078 |
| self_approved     |                 0 |                 22 | 0         |

### Duplicate

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 1 |                 41 | 0.0243902 |
| duplicate_payment |                35 |                 36 | 0.972222  |
| odd_timing        |                 0 |                 35 | 0         |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                 1 |                 51 | 0.0196078 |
| self_approved     |                 0 |                 22 | 0         |

### Below limit

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                41 |                 41 | 1         |
| duplicate_payment |                 1 |                 36 | 0.0277778 |
| odd_timing        |                 0 |                 35 | 0         |
| rare_pairing      |                 0 |                 34 | 0         |
| round_number      |                 1 |                 51 | 0.0196078 |
| self_approved     |                 0 |                 22 | 0         |

### Benford's law

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 1 |                 41 | 0.0243902 |
| duplicate_payment |                 2 |                 36 | 0.0555556 |
| odd_timing        |                 0 |                 35 | 0         |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                 1 |                 51 | 0.0196078 |
| self_approved     |                 0 |                 22 | 0         |

### Round number

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 1 |                 41 | 0.0243902 |
| duplicate_payment |                 2 |                 36 | 0.0555556 |
| odd_timing        |                 0 |                 35 | 0         |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                51 |                 51 | 1         |
| self_approved     |                 0 |                 22 | 0         |

### Any rule

| anomaly_type      |   caught_in_top_k |   total_in_dataset |   recall |
|:------------------|------------------:|-------------------:|---------:|
| below_limit       |                41 |                 41 | 1        |
| duplicate_payment |                35 |                 36 | 0.972222 |
| odd_timing        |                35 |                 35 | 1        |
| rare_pairing      |                 0 |                 34 | 0        |
| round_number      |                51 |                 51 | 1        |
| self_approved     |                22 |                 22 | 1        |

### Logistic Regression

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 0 |                 41 | 0         |
| duplicate_payment |                14 |                 36 | 0.388889  |
| odd_timing        |                35 |                 35 | 1         |
| rare_pairing      |                 3 |                 34 | 0.0882353 |
| round_number      |                 3 |                 51 | 0.0588235 |
| self_approved     |                 0 |                 22 | 0         |

### Isolation Forest

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                 0 |                 41 | 0         |
| duplicate_payment |                 0 |                 36 | 0         |
| odd_timing        |                 3 |                 35 | 0.0857143 |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                 1 |                 51 | 0.0196078 |
| self_approved     |                 0 |                 22 | 0         |

### XGBoost

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                39 |                 41 | 0.95122   |
| duplicate_payment |                14 |                 36 | 0.388889  |
| odd_timing        |                35 |                 35 | 1         |
| rare_pairing      |                 3 |                 34 | 0.0882353 |
| round_number      |                 2 |                 51 | 0.0392157 |
| self_approved     |                 0 |                 22 | 0         |

### Autoencoder

| anomaly_type      |   caught_in_top_k |   total_in_dataset |    recall |
|:------------------|------------------:|-------------------:|----------:|
| below_limit       |                12 |                 41 | 0.292683  |
| duplicate_payment |                11 |                 36 | 0.305556  |
| odd_timing        |                26 |                 35 | 0.742857  |
| rare_pairing      |                 1 |                 34 | 0.0294118 |
| round_number      |                 9 |                 51 | 0.176471  |
| self_approved     |                 0 |                 22 | 0         |

## Which method wins for which anomaly type, and why

**Overall winner: Combining all rules.** The "Any rule" approach achieves the highest PR-AUC of 0.5515 and catches 84% of anomalies in the top 500 entries (recall@500=0.8402), with a precision of 36.8%. Among individual methods, XGBoost (PR-AUC=0.334) outperforms all single rules and other ML models, though it still lags the combined rule baseline.

**Rule specialization reveals a critical insight:** Each rule excels at detecting its specific fraud pattern. The "Below limit" rule catches 100% of below-limit anomalies, the "Odd timing" rule catches all odd-timing entries, and the "Round number" rule catches all round-number anomalies. However, individual rules are fragile—each catches only its targeted pattern and misses others entirely. For example, the "Self-approved" rule catches 100% of self-approved anomalies (22/22) but 0% of duplicate payments, odd timing, and rare pairings.

**Machine learning models show promise but require improvement.** XGBoost generalizes better than rules alone, achieving 95% recall on "below_limit" and perfect recall on "odd_timing," but it fails completely on "self_approved" anomalies (0%). Logistic Regression and Autoencoder perform similarly poorly (PR-AUC 0.1082–0.2576), while Isolation Forest is ineffective (PR-AUC=0.0143), suggesting that unsupervised anomaly detection alone cannot identify domain-specific fraud patterns without feature engineering.

**Benford's law rule (PR-AUC=0.0083) is the weakest method**, catching only 2.3% of anomalies in the top 500. This suggests that the synthetic ledger data does not exhibit significant Benford's law violations, or the threshold (30% deviation) is too strict—a design choice that could be revisited in future work.

**Key trade-off: precision vs. recall.** Individual rules prioritize precision (finding true anomalies when they flag) but sacrifice recall (missing many anomalies). The "Any rule" approach reverses this: it achieves 69% precision@100 and 84% recall@500 but would generate more false positives in production. XGBoost balances the two, with 61% precision@100 and 42% recall@500—a middle ground suitable for investigation workflows where both false positives and false negatives carry cost.

**Why the combined rule approach outperforms ML models:** Rules encode domain knowledge (e.g., "entries posted on weekends are suspicious") that the models must infer from data. The combined ruleset succeeds because it aggregates six independent signals; a true anomaly is more likely to trigger at least one rule than to be detected by a model trained on limited examples of rare fraud patterns. However, this advantage depends on rule quality and comprehensive pattern coverage—Benford's law rule shows how a poorly-designed rule can degrade performance.

## Limitations

The results in this document reflect detection of **planted synthetic anomalies only**, not proven real-world fraud detection performance. 

Key limitations:
- **Synthetic data:** All anomalies were artificially injected following predefined rules. Real fraud is more diverse and may not match our patterns.
- **Class imbalance:** The dataset contains far more normal entries than anomalies. Metrics like precision and recall depend heavily on the threshold chosen.
- **Fixed thresholds:** The approval limit (£10,000), Benford threshold (0.3), and other parameters were arbitrary design choices, not empirically derived from a real control environment.
- **No external validation:** The models and rules have not been tested on real-world data or validated by domain experts.

These limitations do not invalidate the project's technical approach, but they mean any production deployment would require real-world validation before use.

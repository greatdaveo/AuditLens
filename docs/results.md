# Rule performance

Precision is the fraction of a rule's flags that are labelled anomalous. Recall is the fraction of labelled anomalies that the rule flags.

## Precision and recall

| Rule | Precision | Recall |
| --- | --- | --- |
| benfords_law | 0.000 | 0.000 |
| duplicate | 0.500 | 0.188 |
| below_limit | 0.706 | 0.188 |
| odd_timing | 1.000 | 0.259 |
| self_approved | 1.000 | 0.125 |
| round_number | 0.517 | 0.188 |

## Rule catches by anomaly type

Each cell is the number of entries of that true anomaly type flagged by the rule.

| Rule | duplicate_payment | below_limit | odd_timing | self_approved | round_number | rare_pairing |
| --- | --- | --- | --- | --- | --- | --- |
| benfords_law | 0 | 0 | 0 | 0 | 0 | 0 |
| duplicate | 270 | 0 | 0 | 0 | 0 | 0 |
| below_limit | 0 | 270 | 1 | 0 | 0 | 0 |
| odd_timing | 103 | 0 | 270 | 0 | 0 | 0 |
| self_approved | 0 | 0 | 0 | 180 | 0 | 0 |
| round_number | 0 | 0 | 0 | 1 | 270 | 0 |

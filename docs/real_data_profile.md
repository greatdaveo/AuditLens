## Data source and preparation

This analysis uses six monthly Defra spending-over-£25,000 CSV publications, covering September 2025 to February 2026:

- [September 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-september-2025)
- [October 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-october-2025)
- [November 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-november-2025)
- [December 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-december-2025)
- [January 2026](https://www.gov.uk/government/publications/defra-spending-over-25000-january-2026)
- [February 2026](https://www.gov.uk/government/publications/defra-spending-over-25000-february-2026)

The six files contain 5,513 rows. The analysis standardised the date, department, expense type, supplier, and amount fields. Dates were parsed from the formats used in the source files, and amounts were converted to integer pence. The combined data contains 5,490 positive transactions and 22 negative transactions. Negative transactions were kept in the combined dataset but excluded from the positive-amount comparison below.

## Amount comparison

| Metric | Positive Defra transactions (£) | Synthetic expense entries (£) |
|---|---:|---:|
| Count | 5,490 | 45,050 |
| Median | 84,867.50 | 84,631.82 |
| 95th percentile | 916,157.23 | 909,955.14 |
| Coefficient of variation | 10.486 | 2.573 |

For the synthetic data, one expense amount was taken from each generated expense entry. The other journal lines for VAT and trade payables were not counted as additional expenses. Amounts were converted from pence to pounds for this table. The coefficient of variation was calculated as standard deviation divided by mean.

The synthetic median and 95th percentile are close to the corresponding Defra values. The synthetic coefficient of variation is lower, indicating that the synthetic expenses have less relative variation overall.

## Synthetic data settings

The synthetic ledger covers two years, from 1 January 2024, and was generated with seed 42 and 180,000 journal entries. The generated ledger contains 405,050 journal lines and has no unbalanced entries.

The expense amount distribution uses a lognormal model. Its parameters were changed as follows:

| Parameter | Previous value | Current value | Basis for change |
|---|---:|---:|---|
| Expense `mu` | 6.0 | 11.35 | Estimated using the Defra transaction median |
| Expense `sigma` | 1.0 | 1.45 | Estimated using the Defra median and 95th percentile |

Sales retain their original `mu=6.0` and `sigma=1.0` settings because this Defra spending dataset does not provide sales data.

## Interpretation and limitations

The updated expense settings bring the synthetic median and 95th percentile close to the values in the Defra data. However, the coefficient of variation remains lower for the synthetic expenses. Increasing `sigma` enough to match the Defra coefficient of variation would make the synthetic 95th percentile much larger, so the selected settings prioritise matching the median and 95th percentile.

This comparison is a benchmark, not a like-for-like comparison. Defra’s published data represents government spending, including grants and capital spending, while the synthetic ledger represents a simplified company. The real and synthetic datasets also cover different time periods and have different selection rules. In particular, the Defra publication threshold means its amounts do not represent all government spending.
# AuditLens

AuditLens is a learning and research project about finding unusual activity in general-ledger data. It uses accounting rules and, in later stages, machine-learning methods to flag entries for review and explain why they look unusual.

The project starts with a reproducible synthetic ledger. It also profiles public spending data to help assess whether the synthetic expense amounts are plausible. This is an educational prototype: it is not a production audit system, and its results are not evidence of real-world fraud detection.

## What is a general ledger?

A general ledger records an organisation's financial activity. Each business event is recorded as a **journal entry**, which contains one or more **journal lines**.

For example, a sale on credit has two lines:

| Account | Debit | Credit |
|---|---:|---:|
| Trade receivables | Amount of sale | |
| Sales revenue | | Amount of sale |

The debit and credit totals must be equal. This is called double-entry bookkeeping. In AuditLens, `entry_id` identifies the journal entry, while each row in the generated ledger represents one journal line.

Money is stored as integer pence rather than floating-point pounds. For example, £12.34 is stored as `1234` pence. This avoids common rounding problems when computers represent decimal values.

## Project workflow

The project is being built in stages:

1. Generate a clean synthetic ledger and check that entries balance.
2. Add more realistic business behaviour, such as invoices, payroll, VAT, and month-end entries.
3. Profile public spending data and use it to inform the synthetic expense amounts.
4. Add known synthetic anomalies and keep a separate record of which entries were changed.
5. Explore the data, build audit rules and features, and compare detection approaches.

The anomaly-detection and machine-learning work is still in progress. The goal is to test methods against known, deliberately created examples, not to claim that a model can identify real fraud.

## Current project status

The generator creates a two-year ledger using a fixed random seed. With the current settings, it creates 180,000 journal entries and 405,050 journal lines. The generated entries balance.

The generator internally tracks open sales and purchase invoices so customer receipts and supplier payments can be matched to invoices. It also creates payroll, VAT settlement, depreciation, and accrual entries.

A monthly seasonality factor is defined in the generator but is not currently applied when choosing sales events. The invoice-closure tests also need improvement. These are known follow-up items; they do not change the purpose of the Stage 3 spending profile.

The Stage 3 analysis is in [the real-data profiling notebook](notebooks/00_real_data_profile.ipynb), with its written findings in [the profiling report](docs/real_data_profile.md).

## Understanding `mu` and `sigma`

The synthetic generator uses a **lognormal distribution** to create positive, right-skewed amounts: many transactions are around a typical size, while fewer transactions are much larger.

In plain language:

- `mu` controls the typical size of generated amounts. In this project, `mu` is on a logarithmic scale; it is not itself an amount in pounds.
- `sigma` controls how spread out the amounts are. A larger `sigma` creates a wider range, including more very large values.

The generator samples an amount with `rng.lognormvariate(mu, sigma)`, multiplies it by 100 to express it in pence, and stores the result as an integer. With this conversion, `exp(mu)` is approximately the median amount in pounds.

The current settings are separate for sales and expenses:

| Event type | `mu` | `sigma` | Reason |
|---|---:|---:|---|
| Sales | 6.0 | 1.0 | Kept at the original settings; the Defra spending data does not contain sales |
| Expenses | 11.35 | 1.45 | Adjusted using the Defra median and 95th percentile |

The expense settings bring the synthetic median and 95th percentile close to the values in the selected real transactions. The synthetic coefficient of variation is still lower, which means the synthetic amounts have less relative variation overall. Matching all three statistics with one lognormal distribution would require a trade-off.

## Real spending data

The profiling analysis uses six Defra spending-over-£25,000 publications:

- [September 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-september-2025)
- [October 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-october-2025)
- [November 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-november-2025)
- [December 2025](https://www.gov.uk/government/publications/defra-spending-over-25000-december-2025)
- [January 2026](https://www.gov.uk/government/publications/defra-spending-over-25000-january-2026)
- [February 2026](https://www.gov.uk/government/publications/defra-spending-over-25000-february-2026)

The six files contain 5,513 rows. Source amounts are converted to integer pence for analysis. The positive real transactions and all synthetic expense entries compare as follows:

| Metric | Positive Defra transactions (£) | Synthetic expense entries (£) |
|---|---:|---:|
| Count | 5,490 | 45,050 |
| Median | 84,867.50 | 84,631.82 |
| 95th percentile | 916,157.23 | 909,955.14 |
| Coefficient of variation | 10.486 | 2.573 |

This is a benchmark rather than a like-for-like comparison. Defra data includes government grants and capital spending, while the synthetic ledger represents a simplified company. The Defra publications are also subject to a spending threshold, so they do not represent all government spending.

## Project structure

- `src/ledger_audit/` contains the ledger generator, chart of accounts, validation, and modules for later analysis stages.
- `scripts/` contains command-line scripts for generating data and running later project steps.
- `tests/` contains automated checks for the implemented behaviour.
- `notebooks/` contains data exploration and profiling.
- `docs/` contains written findings and project documentation.
- `data/raw/` and `data/processed/` are for generated or downloaded data and are excluded from Git.

## Set up

Run these commands from the project root. They create an isolated Python environment, install the project dependencies, and make the `ledger_audit` package importable.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
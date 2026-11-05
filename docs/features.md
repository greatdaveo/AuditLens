# Features

Each row of `features.csv` is one journal entry. Features that compare an entry with a user's or vendor's history use only entries posted earlier.

| Feature | Type | Meaning | Why it might signal an anomaly |
|---|---|---|---|
| `total_amount_pence` | int | Sum of the entry's debit lines, in pence. | Injected amounts fall in particular ranges, such as just under the approval limit. Expense totals include VAT. |
| `log_amount` | float | Natural log of 1 plus `total_amount_pence`. | Compares small and large entries on one scale, so a few very large amounts do not dominate. |
| `n_lines` | int | Number of journal lines in the entry. | Event types have typical line counts, so this helps judge an amount against similar entries. |
| `hour` | int | Hour of posting, 0 to 23. | Normal entries are posted between 9 and 17; early-morning and late-evening postings are unusual. |
| `is_weekend` | 0/1 | 1 if posted on a Saturday or Sunday. | Normal entries are posted on weekdays. |
| `is_month_end` | 0/1 | 1 if posted in the last two calendar days of the month. | Scheduled entries such as payroll and accruals cluster at month end, so this separates routine entries from ad hoc ones. |
| `user_amount_zscore` | float | Standard deviations between this amount and the user's earlier amounts; 0 when there is no usable history. | An amount far from what a user normally posts is unusual for that person. |
| `user_hour_typicality` | float | Share of the user's earlier entries posted at this hour; 1.0 for a user's first entry. | A low value means the user rarely posts at this hour. |
| `days_since_similar` | float | Days since the user's last entry on the same set of accounts; 999 if there is none. | Very short gaps can indicate repeated entries; a long or missing gap marks an account combination the user rarely uses. |
| `vendor_entry_count_so_far` | int | Earlier entries for the same vendor; 0 when there is no vendor. | Repeat activity with one vendor can indicate duplicates, and a vendor's first entry is a new relationship. |
| `user_id_U02` to `user_id_U08` | 0/1 | One-hot encoding of the posting user; `U01` is the baseline when all are 0. | Lets a model learn patterns specific to a user. |
| `weekday_1` to `weekday_6` | 0/1 | One-hot encoding of the weekday, 0 = Monday; Monday is the baseline when all are 0. | Lets a model learn day-of-week patterns, especially Saturday (5) and Sunday (6). |
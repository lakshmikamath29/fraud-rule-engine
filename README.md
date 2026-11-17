# Fraud Rule Engine (synthetic data)

## Rule catalog
- R001: new beneficiary AND amount >= 25,000 -> flag
- R002: 5 or more transactions by one customer within 10 minutes -> flag
- R003: hour between 00:00 and 04:59 AND amount >= 20,000 -> flag
- R004: new device AND city change AND amount >= 10,000 -> flag

## Testing
7 UAT test cases cover boundary values and negative cases for each rule (amount thresholds, time-window edges, per-customer velocity, all-conditions-required).
Run with: python -m pytest -v tests
Deliberately changing >= to > in R001 made TC-001 fail, confirming the tests catch off-by-one logic errors.

## How to run
    python3 -m venv venv && source venv/bin/activate
    pip install pandas numpy pytest streamlit
    python -m src.generate_data
    python -m src.evaluate

## Findings (synthetic data, 5,118 transactions, 118 fraud)
- The 4 rules raised 79 alerts and caught 78 of 118 fraud transactions (66%).
- R001 and R002 had precision 1.0. R003 had precision 0.952 (1 false positive).
- R004 (new device + city change) raised 0 alerts because the data has no matching fraud pattern. It is flagged REVIEW / TUNE. In production I would check whether the rule is wrong or the pattern simply has not occurred.
- R002 fires from the 5th transaction in a burst, so it catches every incident but misses the first 4 transactions of each. Only 49% of velocity fraud was caught at transaction level. Lowering the count to 3 raised recall from 0.32 to 0.49 with precision still 1.0 here, but on real data it would likely add false positives.
- R003 shows the precision/recall trade-off: a 5,000 threshold gave 155 alerts at 0.129 precision, while 20,000 gave 21 alerts at 0.952.
- R001 at a 10,000 threshold dropped precision to 0.8 with no recall gain, so 25,000 is the better setting.

## Limitations
- All data is synthetic, so precision and recall here do not predict real-world performance.
- Each rule only targets one pattern, so per-rule recall is low by design.

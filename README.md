# Fraud Rule Engine (synthetic data)

## Rule catalog
- R001: new beneficiary AND amount >= 25,000 -> flag
- R002: 5 or more transactions by one customer within 10 minutes -> flag
- R003: hour between 00:00 and 04:59 AND amount >= 20,000 -> flag
- R004: new device AND city change AND amount >= 10,000 -> flag

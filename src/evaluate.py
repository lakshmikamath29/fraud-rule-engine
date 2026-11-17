import os
import sqlite3
import pandas as pd
from src.rules import RULES, apply_rules

MIN_PRECISION = 0.10  # rules below this are flagged for review

# which config parameter to vary for which rule (used for threshold tuning)
SWEEP_RULE = {
    "new_benef_amount": "R001",
    "velocity_count": "R002",
    "night_amount": "R003",
    "device_city_amount": "R004",
}


def rule_performance(df, flags):
    total_fraud = int(df.is_fraud.sum())
    rows = []
    for rid, (name, _) in RULES.items():
        hit = flags[rid]
        alerts = int(hit.sum())
        tp = int((hit & (df.is_fraud == 1)).sum())
        precision = tp / alerts if alerts else 0.0
        recall = tp / total_fraud
        status = "REVIEW / TUNE" if (alerts == 0 or precision < MIN_PRECISION) else "OK"
        rows.append(dict(rule_id=rid, rule=name, alerts=alerts, true_positives=tp,
                         false_positives=alerts - tp, precision=round(precision, 3),
                         recall=round(recall, 3), status=status))
    return pd.DataFrame(rows)


def sweep(df, param, values):
    """Try different threshold values for one rule and record precision/recall."""
    rid = SWEEP_RULE[param]
    total_fraud = int(df.is_fraud.sum())
    rows = []
    for v in values:
        hit = apply_rules(df, {param: v})[rid]
        alerts = int(hit.sum())
        tp = int((hit & (df.is_fraud == 1)).sum())
        rows.append(dict(rule_id=rid, param=param, value=v, alerts=alerts,
                         precision=round(tp / alerts, 3) if alerts else 0.0,
                         recall=round(tp / total_fraud, 3)))
    return pd.DataFrame(rows)


def main():
    os.makedirs("outputs", exist_ok=True)
    df = pd.read_csv("data/transactions.csv", parse_dates=["ts"])
    flags = apply_rules(df)

    # 1. Per-rule performance
    perf = rule_performance(df, flags)
    perf.to_csv("outputs/rule_performance.csv", index=False)
    print(perf.to_string(index=False))

    # 2. Overall coverage
    any_hit = flags.any(axis=1)
    caught = int((any_hit & (df.is_fraud == 1)).sum())
    print(f"\nTotal alerts: {int(any_hit.sum())} | fraud caught: {caught}/{int(df.is_fraud.sum())}")

    # 3. Which fraud types are caught?
    print("\nShare of each fraud type caught by at least one rule:")
    fr = df[df.is_fraud == 1].assign(caught=any_hit[df.is_fraud == 1])
    print(fr.groupby("fraud_type")["caught"].mean().round(2).to_string())

    # 4. Threshold tuning
    tuning = pd.concat([
        sweep(df, "new_benef_amount", [10000, 25000, 50000, 75000]),
        sweep(df, "velocity_count", [3, 4, 5, 6, 8]),
        sweep(df, "night_amount", [5000, 10000, 20000, 40000]),
    ])
    tuning.to_csv("outputs/threshold_tuning.csv", index=False)
    print("\nThreshold tuning:")
    print(tuning.to_string(index=False))

    # 5. Save to SQLite for the SQL step
    long = flags.stack().reset_index()
    long.columns = ["row", "rule_id", "hit"]
    alerts_tbl = long[long.hit].merge(df[["txn_id"]], left_on="row", right_index=True)[["txn_id", "rule_id"]]
    alerts_tbl.to_csv("outputs/alerts.csv", index=False)
    con = sqlite3.connect("outputs/fraud.db")
    df.to_sql("transactions", con, if_exists="replace", index=False)
    alerts_tbl.to_sql("alerts", con, if_exists="replace", index=False)
    con.close()


if __name__ == "__main__":
    main()

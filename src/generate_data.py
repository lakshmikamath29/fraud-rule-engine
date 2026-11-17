import numpy as np
import pandas as pd

rng = np.random.default_rng(42)  # fixed seed so results repeat
START = pd.Timestamp("2026-10-01")
CHANNELS = ["UPI", "IMPS", "NEFT", "CARD"]


def random_times(n):
    secs = rng.integers(0, 30 * 24 * 3600, n)  # random second within 30 days
    return START + pd.to_timedelta(secs, unit="s")


def generate(n_normal=5000, n_customers=200):
    # 1. Normal transactions
    df = pd.DataFrame({
        "customer_id": [f"C{i:04d}" for i in rng.integers(0, n_customers, n_normal)],
        "ts": random_times(n_normal),
        "channel": rng.choice(CHANNELS, n_normal, p=[0.5, 0.2, 0.1, 0.2]),
        "amount": rng.lognormal(np.log(2000), 0.8, n_normal).round(2),
        "is_new_beneficiary": (rng.random(n_normal) < 0.04).astype(int),
        "is_new_device": (rng.random(n_normal) < 0.02).astype(int),
        "city_change": (rng.random(n_normal) < 0.015).astype(int),
    })
    df["is_fraud"] = 0
    df["fraud_type"] = ""

    # 2. Fraud patterns
    frauds = []

    def cust():
        return f"C{rng.integers(0, n_customers):04d}"

    def day_time(h_low, h_high):
        return START + pd.Timedelta(days=int(rng.integers(0, 30)),
                                    hours=int(rng.integers(h_low, h_high)),
                                    minutes=int(rng.integers(0, 60)))

    # Pattern A: velocity - 6-10 small UPI txns within ~8 minutes
    for _ in range(10):
        c, t0 = cust(), day_time(8, 20)
        for s in np.sort(rng.integers(0, 480, rng.integers(6, 11))):
            frauds.append(dict(
                customer_id=c, ts=t0 + pd.Timedelta(seconds=int(s)), channel="UPI",
                amount=round(float(rng.uniform(500, 5000)), 2),
                is_new_beneficiary=1, is_new_device=0, city_change=0,
                is_fraud=1, fraud_type="velocity"))

    # Pattern B: large payment to a new beneficiary
    for _ in range(20):
        frauds.append(dict(
            customer_id=cust(), ts=day_time(8, 22), channel=str(rng.choice(["UPI", "IMPS"])),
            amount=round(float(rng.uniform(30000, 150000)), 2),
            is_new_beneficiary=1, is_new_device=0, city_change=0,
            is_fraud=1, fraud_type="new_benef_high"))

    # Pattern C: high-value payment between 1 a.m. and 4 a.m.
    for _ in range(20):
        frauds.append(dict(
            customer_id=cust(), ts=day_time(1, 5), channel="IMPS",
            amount=round(float(rng.uniform(20000, 80000)), 2),
            is_new_beneficiary=0, is_new_device=0, city_change=0,
            is_fraud=1, fraud_type="night_high"))

    out = pd.concat([df, pd.DataFrame(frauds)], ignore_index=True)
    out = out.sort_values("ts").reset_index(drop=True)
    out.insert(0, "txn_id", [f"T{i:06d}" for i in range(len(out))])
    return out


if __name__ == "__main__":
    d = generate()
    d.to_csv("data/transactions.csv", index=False)
    print(len(d), "rows | fraud rate:", round(d.is_fraud.mean(), 4))

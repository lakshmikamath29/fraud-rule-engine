import numpy as np
import pandas as pd

# All thresholds live here, so rules can be tuned without touching the logic
CONFIG = {
    "new_benef_amount": 25000,
    "velocity_count": 5,
    "velocity_window_min": 10,
    "night_start_hour": 0,
    "night_end_hour": 4,
    "night_amount": 20000,
    "device_city_amount": 10000,
}


def r001_new_benef_high(df, c):
    return (df.is_new_beneficiary == 1) & (df.amount >= c["new_benef_amount"])


def r002_velocity(df, c):
    out = pd.Series(False, index=df.index)
    window = c["velocity_window_min"] * 60  # seconds
    for _, g in df.groupby("customer_id"):
        g = g.sort_values("ts")
        t = (g["ts"] - g["ts"].min()).dt.total_seconds().to_numpy()
        # for each txn: how many of this customer's txns fall in the last window (including itself)
        count = np.arange(len(t)) - np.searchsorted(t, t - window, side="left") + 1
        out.loc[g.index] = count >= c["velocity_count"]
    return out


def r003_night_high(df, c):
    hour = df.ts.dt.hour
    return hour.between(c["night_start_hour"], c["night_end_hour"]) & (df.amount >= c["night_amount"])


def r004_device_city(df, c):
    return (df.is_new_device == 1) & (df.city_change == 1) & (df.amount >= c["device_city_amount"])


RULES = {
    "R001": ("New beneficiary + high value", r001_new_benef_high),
    "R002": ("Velocity burst", r002_velocity),
    "R003": ("Night-time high value", r003_night_high),
    "R004": ("New device + city change", r004_device_city),
}


def apply_rules(df, cfg=None):
    cfg = {**CONFIG, **(cfg or {})}
    return pd.DataFrame({rid: fn(df, cfg) for rid, (_, fn) in RULES.items()}, index=df.index)


if __name__ == "__main__":
    df = pd.read_csv("data/transactions.csv", parse_dates=["ts"])
    flags = apply_rules(df)
    for rid, (name, _) in RULES.items():
        print(rid, name, "->", int(flags[rid].sum()), "alerts")

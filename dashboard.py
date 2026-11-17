import pandas as pd
import streamlit as st
from src.rules import CONFIG, apply_rules
from src.evaluate import rule_performance

st.set_page_config(page_title="Fraud Rule Monitor", layout="wide")
st.title("Transaction Monitoring: Rule Performance")
st.caption("Synthetic data. Move the sliders to tune thresholds and watch precision/recall change.")


@st.cache_data
def load():
    return pd.read_csv("data/transactions.csv", parse_dates=["ts"])


df = load()

st.sidebar.header("Tune thresholds")
cfg = {
    "new_benef_amount": st.sidebar.slider("R001 min amount (new beneficiary)", 5000, 100000, CONFIG["new_benef_amount"], 5000),
    "velocity_count": st.sidebar.slider("R002 txns in 10 min", 2, 10, CONFIG["velocity_count"]),
    "night_amount": st.sidebar.slider("R003 night min amount", 5000, 100000, CONFIG["night_amount"], 5000),
    "device_city_amount": st.sidebar.slider("R004 min amount (new device + city change)", 1000, 50000, CONFIG["device_city_amount"], 1000),
}

flags = apply_rules(df, cfg)
perf = rule_performance(df, flags)
any_hit = flags.any(axis=1)
caught = int((any_hit & (df.is_fraud == 1)).sum())
total_alerts = int(any_hit.sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{len(df):,}")
c2.metric("Total alerts", total_alerts)
c3.metric("Fraud caught", f"{caught / int(df.is_fraud.sum()):.0%}")
c4.metric("Overall precision", f"{caught / max(total_alerts, 1):.0%}")

st.subheader("Rule performance")
st.dataframe(perf)

left, right = st.columns(2)
left.subheader("Alerts by rule")
left.bar_chart(perf.set_index("rule_id")["alerts"])
right.subheader("Precision vs recall")
right.bar_chart(perf.set_index("rule_id")[["precision", "recall"]], stack=False)

st.subheader("Daily alert volume")
st.line_chart(any_hit.groupby(df.ts.dt.date).sum())

st.subheader("Fraud missed by every rule")
missed = df[(df.is_fraud == 1) & ~any_hit].groupby("fraud_type").size().rename("missed").reset_index()
if missed.empty:
    st.success("No fraud missed at these thresholds.")
else:
    st.dataframe(missed)

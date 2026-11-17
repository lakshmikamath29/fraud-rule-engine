import pandas as pd
from src.rules import CONFIG, r001_new_benef_high, r002_velocity, r003_night_high, r004_device_city


def mk(rows):
    """Build a tiny DataFrame; any column not given gets a harmless default."""
    d = pd.DataFrame(rows)
    d["ts"] = pd.to_datetime(d["ts"])
    for col, default in [("customer_id", "C1"), ("amount", 100), ("is_new_beneficiary", 0),
                         ("is_new_device", 0), ("city_change", 0)]:
        if col not in d:
            d[col] = default
    return d


def test_r001_amount_boundary():  # TC-001
    d = mk([dict(ts="2026-10-05 12:00", amount=24999, is_new_beneficiary=1),
            dict(ts="2026-10-05 12:01", amount=25000, is_new_beneficiary=1),
            dict(ts="2026-10-05 12:02", amount=90000, is_new_beneficiary=0)])
    assert r001_new_benef_high(d, CONFIG).tolist() == [False, True, False]


def test_r002_fires_on_5th_txn_in_window():  # TC-002
    d = mk([dict(ts=f"2026-10-05 12:0{i}:00") for i in range(5)])
    assert r002_velocity(d, CONFIG).tolist() == [False, False, False, False, True]


def test_r002_not_fired_when_spread_out():  # TC-003
    d = mk([dict(ts=f"2026-10-05 {h}:00:00") for h in range(10, 15)])
    assert not r002_velocity(d, CONFIG).any()


def test_r002_not_fired_across_different_customers():  # TC-004
    d = mk([dict(ts=f"2026-10-05 12:0{i}:00", customer_id=f"C{i}") for i in range(5)])
    assert not r002_velocity(d, CONFIG).any()


def test_r003_time_window_edges():  # TC-005
    d = mk([dict(ts="2026-10-05 04:59", amount=30000),
            dict(ts="2026-10-05 05:00", amount=30000)])
    assert r003_night_high(d, CONFIG).tolist() == [True, False]


def test_r003_amount_boundary():  # TC-006
    d = mk([dict(ts="2026-10-05 02:00", amount=19999),
            dict(ts="2026-10-05 02:01", amount=20000)])
    assert r003_night_high(d, CONFIG).tolist() == [False, True]


def test_r004_requires_all_conditions():  # TC-007
    d = mk([dict(ts="2026-10-05 12:00", amount=20000, is_new_device=1, city_change=1),
            dict(ts="2026-10-05 12:01", amount=20000, is_new_device=1, city_change=0),
            dict(ts="2026-10-05 12:02", amount=20000, is_new_device=0, city_change=1),
            dict(ts="2026-10-05 12:03", amount=5000, is_new_device=1, city_change=1)])
    assert r004_device_city(d, CONFIG).tolist() == [True, False, False, False]

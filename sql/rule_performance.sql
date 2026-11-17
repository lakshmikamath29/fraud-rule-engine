-- 1. Precision per rule (worst first)
SELECT a.rule_id,
       COUNT(*)                                   AS alerts,
       SUM(t.is_fraud)                            AS true_positives,
       COUNT(*) - SUM(t.is_fraud)                 AS false_positives,
       ROUND(1.0 * SUM(t.is_fraud) / COUNT(*), 3) AS precision
FROM alerts a
JOIN transactions t ON a.txn_id = t.txn_id
GROUP BY a.rule_id
ORDER BY precision ASC;

-- 2. Daily alert volume
SELECT DATE(t.ts) AS day, COUNT(*) AS alerts
FROM alerts a
JOIN transactions t ON a.txn_id = t.txn_id
GROUP BY day
ORDER BY day;

-- 3. Fraud missed by every rule
SELECT fraud_type, COUNT(*) AS missed
FROM transactions
WHERE is_fraud = 1
  AND txn_id NOT IN (SELECT txn_id FROM alerts)
GROUP BY fraud_type
ORDER BY missed DESC;

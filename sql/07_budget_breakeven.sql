-- 07_budget_breakeven.sql
-- Without spend data, how much more could each channel cost per session and still beat paid social?
-- Break-even multiple = channel pipeline per 1,000 real sessions / paid social pipeline per 1,000 real sessions.
-- A channel with a multiple of 12 produces more pipeline per dollar than paid social unless its
-- sessions cost more than 12 times as much.
CREATE OR REPLACE VIEW budget_breakeven AS
WITH ps AS (
    SELECT pipeline_per_1000_sessions AS ps_rate FROM corrected_funnel WHERE channel = 'Paid social'
)
SELECT channel,
       human_sessions,
       pipeline,
       pipeline_per_1000_sessions,
       ROUND(pipeline_per_1000_sessions / ps.ps_rate, 1) AS breakeven_cost_multiple_vs_paid_social
FROM corrected_funnel, ps
WHERE channel <> 'Unresolved'
ORDER BY pipeline_per_1000_sessions DESC;

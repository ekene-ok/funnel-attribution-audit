-- 06_corrected_funnel.sql
-- The funnel by channel after the fixes: bot sessions removed, duplicates removed, real channels.

CREATE OR REPLACE VIEW corrected_funnel AS
WITH s AS (
    SELECT channel, COUNT(*) FILTER (WHERE NOT likely_bot) AS human_sessions, COUNT(*) AS all_sessions
    FROM sessions_flagged GROUP BY channel
),
f AS (
    SELECT r.reconstructed_channel AS channel, COUNT(*) AS leads, SUM(f.is_mql::INT) AS mqls,
           SUM(f.is_opportunity::INT) AS opportunities, SUM(f.is_won::INT) AS won,
           SUM(f.pipeline_amount) AS pipeline
    FROM leads_reconstructed r JOIN crm_funnel f USING (lead_id) GROUP BY 1
)
SELECT f.channel, s.all_sessions, s.human_sessions, f.leads, f.mqls, f.opportunities, f.won,
       ROUND(f.pipeline, 0)                                      AS pipeline,
       ROUND(f.leads / NULLIF(s.all_sessions, 0), 4)             AS lead_rate_as_reported,
       ROUND(f.leads / NULLIF(s.human_sessions, 0), 4)           AS lead_rate_human_sessions,
       ROUND(1000 * f.pipeline / NULLIF(s.human_sessions, 0), 0) AS pipeline_per_1000_sessions
FROM f LEFT JOIN s USING (channel)
ORDER BY pipeline_per_1000_sessions DESC NULLS LAST;

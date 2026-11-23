-- 05_reconciliation.sql
-- Reported vs reconstructed results by channel, and why the two differ.

CREATE OR REPLACE VIEW reconciliation_by_channel AS
WITH rep AS (
    SELECT l.lead_source AS channel, SUM(f.is_mql::INT) AS reported_mqls,
           SUM(f.pipeline_amount) AS reported_pipeline
    FROM crm_leads l JOIN crm_funnel f USING (lead_id) GROUP BY 1
),
rec AS (
    SELECT r.reconstructed_channel AS channel, SUM(f.is_mql::INT) AS true_mqls,
           SUM(f.pipeline_amount) AS true_pipeline
    FROM leads_reconstructed r JOIN crm_funnel f USING (lead_id) GROUP BY 1
)
SELECT rec.channel,
       COALESCE(rep.reported_mqls, 0)                                AS reported_mqls,
       rec.true_mqls,
       ROUND(rec.true_mqls / NULLIF(COALESCE(rep.reported_mqls, 0), 0), 2) AS mql_undercount_factor,
       ROUND(COALESCE(rep.reported_pipeline, 0), 0)                  AS reported_pipeline,
       ROUND(rec.true_pipeline, 0)                                   AS true_pipeline,
       ROUND(1 - COALESCE(rep.reported_pipeline, 0) / NULLIF(rec.true_pipeline, 0), 3) AS share_of_pipeline_missing
FROM rec LEFT JOIN rep USING (channel)
ORDER BY true_pipeline DESC;

CREATE OR REPLACE VIEW misattribution_root_causes AS
SELECT attribution_status,
       COUNT(*)                                 AS leads,
       SUM(f.is_mql::INT)                       AS mqls,
       ROUND(SUM(f.pipeline_amount), 0)         AS pipeline,
       ROUND(SUM(f.pipeline_amount) / SUM(SUM(f.pipeline_amount)) OVER (), 3) AS share_of_all_pipeline
FROM leads_reconstructed r JOIN crm_funnel f USING (lead_id)
GROUP BY attribution_status
ORDER BY pipeline DESC;

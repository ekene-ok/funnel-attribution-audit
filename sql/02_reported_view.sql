-- 02_reported_view.sql
-- What the marketing dashboard shows today: everything grouped by the CRM lead source field.
CREATE OR REPLACE VIEW reported_by_source AS
SELECT COALESCE(NULLIF(l.lead_source, ''), '(blank)')   AS lead_source,
       COUNT(*)                                          AS leads,
       SUM(f.is_mql::INT)                                AS mqls,
       SUM(f.is_opportunity::INT)                        AS opportunities,
       ROUND(SUM(f.pipeline_amount), 0)                  AS pipeline
FROM crm_leads l JOIN crm_funnel f USING (lead_id)
GROUP BY 1
ORDER BY pipeline DESC;

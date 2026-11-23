-- 03_data_quality.sql
-- Checks that reveal each defect from the data itself.

-- A. Sources that are not real acquisition channels, or are missing.
CREATE OR REPLACE VIEW dq_suspicious_sources AS
SELECT COALESCE(NULLIF(lead_source, ''), '(blank)') AS lead_source,
       captured_via, form_name, passed_routing,
       COUNT(*) AS leads
FROM crm_leads
WHERE lead_source IN ('', 'Direct', 'Sales Inbound') OR lead_source IS NULL
GROUP BY ALL
ORDER BY leads DESC;

-- B. Duplicate leads: the same email creating more than one lead within 7 days.
CREATE OR REPLACE VIEW lead_dedup AS
SELECT *,
       ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at) AS nth_record,
       created_at - FIRST_VALUE(created_at) OVER (PARTITION BY email ORDER BY created_at) AS since_first
FROM crm_leads;

CREATE OR REPLACE VIEW dq_duplicates AS
SELECT COUNT(*) FILTER (WHERE nth_record > 1 AND since_first <= INTERVAL 7 DAY) AS duplicate_leads,
       COUNT(*)                                                                AS total_lead_records,
       ROUND(COUNT(*) FILTER (WHERE nth_record > 1 AND since_first <= INTERVAL 7 DAY) / COUNT(*), 3) AS duplicate_share
FROM lead_dedup;

-- C. Likely bot sessions: under 5 seconds and a single page.
CREATE OR REPLACE VIEW sessions_flagged AS
SELECT *, (duration_sec < 5 AND pages_viewed = 1) AS likely_bot
FROM web_sessions;

CREATE OR REPLACE VIEW dq_bots_by_channel AS
SELECT channel,
       COUNT(*)                                   AS sessions,
       SUM(likely_bot::INT)                       AS likely_bot_sessions,
       ROUND(AVG(likely_bot::INT), 3)             AS likely_bot_share
FROM sessions_flagged
GROUP BY channel
ORDER BY likely_bot_share DESC;

-- D. How many leads can be linked back to a web session.
CREATE OR REPLACE VIEW dq_linkage AS
SELECT ROUND(AVG((visitor_id IS NOT NULL)::INT), 3) AS share_linkable_to_web_session
FROM crm_leads;

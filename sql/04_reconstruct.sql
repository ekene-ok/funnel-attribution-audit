-- 04_reconstruct.sql
-- Rebuild each lead's real channel from the web session that created it, and remove duplicates.
-- Rule: if the lead links to a web session, use that session's channel. If not, keep the CRM
-- source when it is a real channel; otherwise mark it "Unresolved" rather than guess.

CREATE OR REPLACE VIEW leads_reconstructed AS
WITH first_session AS (
    SELECT visitor_id, channel
    FROM web_sessions
    QUALIFY ROW_NUMBER() OVER (PARTITION BY visitor_id ORDER BY session_start) = 1
)
SELECT d.lead_id, d.email, d.captured_via, d.form_name, d.passed_routing,
       COALESCE(NULLIF(d.lead_source, ''), '(blank)')               AS reported_source,
       COALESCE(s.channel,
                CASE WHEN d.lead_source IN ('', 'Direct', 'Sales Inbound') OR d.lead_source IS NULL
                     THEN 'Unresolved' ELSE d.lead_source END)      AS reconstructed_channel,
       CASE
           WHEN s.channel IS NULL                                         THEN 'Not linkable'
           WHEN s.channel = d.lead_source                                 THEN 'Correct'
           WHEN d.captured_via = 'chat'                                   THEN 'Chat widget dropped campaign tags'
           WHEN d.passed_routing AND d.lead_source = 'Sales Inbound'      THEN 'Lead routing overwrote source'
           WHEN COALESCE(d.lead_source, '') = ''                          THEN 'Form left source blank'
           ELSE 'Other mismatch'
       END                                                          AS attribution_status
FROM lead_dedup d
LEFT JOIN first_session s USING (visitor_id)
WHERE NOT (d.nth_record > 1 AND d.since_first <= INTERVAL 7 DAY);

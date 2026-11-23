-- 01_load.sql: raw tables exactly as exported from the web analytics tool and the CRM.
CREATE OR REPLACE TABLE web_sessions AS SELECT * FROM read_csv_auto('data/web_sessions.csv');
CREATE OR REPLACE TABLE crm_leads    AS SELECT * FROM read_csv_auto('data/crm_leads.csv', types={'lead_source': 'VARCHAR', 'visitor_id': 'BIGINT'});
CREATE OR REPLACE TABLE crm_funnel   AS SELECT * FROM read_csv_auto('data/crm_funnel.csv');

"""Run the audit SQL, export results, and validate the reconstruction against ground truth."""
from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
con = duckdb.connect()
con.execute(f"SET file_search_path = '{ROOT}'")
for f in sorted((ROOT / "sql").glob("*.sql")):
    con.execute(f.read_text())
VIEWS = ["reported_by_source", "dq_suspicious_sources", "dq_duplicates", "dq_bots_by_channel", "dq_linkage",
         "reconciliation_by_channel", "misattribution_root_causes", "corrected_funnel", "budget_breakeven"]
for v in VIEWS:
    con.sql(f"SELECT * FROM {v}").write_csv(str(OUT / f"{v}.csv"))

# Validation (the audit never reads the truth files; this step only checks it).
rec = con.sql("SELECT lead_id, reconstructed_channel FROM leads_reconstructed").df()
truth = pd.read_csv(ROOT / "data" / "_truth_leads.csv")
m = rec.merge(truth, on="lead_id")
resolved = m[m["reconstructed_channel"] != "Unresolved"]
bots = con.sql("SELECT session_id, likely_bot FROM sessions_flagged").df().merge(
    pd.read_csv(ROOT / "data" / "_truth_bots.csv"), on="session_id")
val = pd.DataFrame([
    {"check": "Leads with a resolved channel", "value": round(len(resolved) / len(m), 3)},
    {"check": "Accuracy of resolved channels vs truth", "value": round((resolved["reconstructed_channel"] == resolved["true_channel"]).mean(), 3)},
    {"check": "Bot sessions caught (recall)", "value": round(bots.loc[bots["_is_bot"] == 1, "likely_bot"].mean(), 3)},
    {"check": "Human sessions wrongly flagged as bots", "value": round(bots.loc[bots["_is_bot"] == 0, "likely_bot"].mean(), 4)},
])
val.to_csv(OUT / "validation.csv", index=False)
pd.set_option("display.width", 220)
for v in VIEWS:
    print(f"\n== {v}"); print(con.sql(f"SELECT * FROM {v}").df().to_string(index=False))
print("\n== validation"); print(val.to_string(index=False))

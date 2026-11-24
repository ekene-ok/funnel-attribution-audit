"""README charts: one message per chart, one highlight colour, direct labels."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
import brand_style as b

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "results", ROOT / "charts"
OUT.mkdir(exist_ok=True)
HL = b.PROJECT["funnel-attribution-audit"]
SRC = "Synthetic B2B SaaS funnel, six months; audit SQL in sql/"

# Chart 1: share of each channel's real pipeline missing from reports
r = pd.read_csv(RES / "reconciliation_by_channel.csv")
r = r[~r["channel"].isin(["Direct", "Unresolved"])].sort_values("share_of_pipeline_missing", ascending=False)
fig, ax = b.chart(height=4.6, label_in=1.3)
b.hbar(ax, r.channel.tolist(), (r.share_of_pipeline_missing * 100).tolist(), {0}, lambda v: f"{v:.0f}%", HL)
b.titles(fig, "The dashboard shows none of the $1.16M pipeline from in-app messages",
         "Share of each channel's sales pipeline missing from the marketing dashboard")
b.credit(fig, SRC)
b.save(fig, OUT / "01_pipeline_missing_by_channel.png")

# Chart 2: where the misattributed pipeline comes from
c = pd.read_csv(RES / "misattribution_root_causes.csv").set_index("attribution_status")
order = ["Correct", "Chat widget dropped campaign tags", "Lead routing overwrote source", "Form left source blank",
         "Not linkable"]
labels = ["Credited correctly", "Chat widget", "Lead routing", "Sign-up form", "No web visit"]
subs = ["", "drops campaign tags", "overwrites the source", "leaves source blank", "nothing to trace"]
fig, ax = b.chart(height=4.4, label_in=1.45)
b.hbar(ax, labels, [c.loc[o, "share_of_all_pipeline"] * 100 for o in order], {1}, lambda v: f"{v:.0f}%", HL, sublabels=subs)
b.titles(fig, "Only 38% of pipeline is credited to the right channel",
         "Share of all sales pipeline, by why its channel was lost. The chat widget is the biggest leak")
b.credit(fig, SRC)
b.save(fig, OUT / "02_root_causes.png")
print("Charts saved to charts/")

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
SURFACE, INK, INK2 = "#ffffff", b.INK, b.MUTED
HIGHLIGHT, CONTEXT = b.PROJECT["funnel-attribution-audit"], b.CONTEXT
plt.rcParams.update({"font.family": "sans-serif", "font.size": 11, "text.color": INK,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})


def titles(fig, title, subtitle):
    fig.text(0.03, 0.97, title, fontsize=15, va="top")
    fig.text(0.03, 0.885, subtitle, fontsize=10.5, color=INK2, va="top")


def hbars(ax, labels, vals, hi, fmt, xmax):
    ax.barh(labels, vals, height=0.55, color=[HIGHLIGHT if i == hi else CONTEXT for i in range(len(vals))])
    for y, v in enumerate(vals):
        ax.text(v + xmax * 0.012, y, fmt(v), va="center", fontsize=12 if y == hi else 11, color=INK if y == hi else INK2)
    for i, lbl in enumerate(ax.get_yticklabels()):
        lbl.set_color(INK if i == hi else INK2)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, pad=8)
    ax.set_xlim(0, xmax)


# Chart 1: share of each channel's real pipeline missing from reports
r = pd.read_csv(RES / "reconciliation_by_channel.csv")
r = r[~r["channel"].isin(["Direct", "Unresolved"])].sort_values("share_of_pipeline_missing")
hi = len(r) - 1
fig, ax = plt.subplots(figsize=(9, 4.9))
hbars(ax, r["channel"], r["share_of_pipeline_missing"] * 100, hi, lambda v: f"{v:.0f}%", 115)
titles(fig, "Reports show none of the pipeline from in-app messages",
       "Share of each channel's real pipeline missing from the marketing dashboard. In-app\n"
       "messages drove \\$1.16M in pipeline; the dashboard credited them with \\$0.")
fig.subplots_adjust(left=0.2, right=0.97, top=0.75, bottom=0.1)
b.source(fig, "Synthetic B2B SaaS funnel, six months; audit SQL in sql/")
fig.savefig(OUT / "01_pipeline_missing_by_channel.png", dpi=200)
plt.close(fig)

# Chart 2: where the misattributed pipeline comes from
c = pd.read_csv(RES / "misattribution_root_causes.csv").set_index("attribution_status")
order = ["Not linkable", "Form left source blank", "Lead routing overwrote source",
         "Chat widget dropped campaign tags", "Correct"]
labels = {"Correct": "Attributed correctly", "Chat widget dropped campaign tags": "Chat widget drops tags",
          "Lead routing overwrote source": "Routing overwrites source", "Form left source blank": "Form leaves source blank",
          "Not linkable": "No web visit to link"}
vals = [c.loc[o, "share_of_all_pipeline"] * 100 for o in order]
fig, ax = plt.subplots(figsize=(9, 4.9))
hbars(ax, [labels[o] for o in order], vals, 3, lambda v: f"{v:.0f}%", 48)
titles(fig, "Only 38% of pipeline is credited to the right channel",
       "Share of all pipeline by attribution status. The chat widget is the biggest single leak.")
fig.subplots_adjust(left=0.29, right=0.97, top=0.79, bottom=0.1)
b.source(fig, "Synthetic B2B SaaS funnel, six months; audit SQL in sql/")
fig.savefig(OUT / "02_root_causes.png", dpi=200)
plt.close(fig)
print("Charts saved to charts/")

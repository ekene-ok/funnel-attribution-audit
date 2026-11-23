"""Generate a realistic B2B SaaS marketing funnel with known tracking defects.

Tables written to data/ (CSV):
  web_sessions   one row per website session, with the channel recorded at the time
                 (from campaign tags or referrer), visitor id, duration and pages viewed
  crm_leads      one row per lead record in the CRM, with the lead source the CRM recorded,
                 how the lead was captured (form or chat) and whether it passed through routing
  crm_funnel     MQL, opportunity and closed-won outcomes per lead, with pipeline amount

Defects built in (the audit has to find these from the data alone):
  1. Chat widget drops campaign tags, so chat leads are recorded as "Direct"
  2. Lead routing overwrites the original source with "Sales Inbound" for routed leads
  3. One form (the in-app request form) has no hidden source field, so source is blank
  4. Some people submit twice, creating duplicate lead records
  5. Bot clicks inflate paid social sessions (very short, single-page sessions)
Realistic limit: 10% of leads have no visitor id (cookies blocked), so not every lead can be
linked back to its web session.
A ground-truth file (data/_truth_leads.csv) records each lead's real channel so the audit's
reconstruction can be validated. The audit SQL never reads it.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(2026)

CHANNELS = {  # monthly sessions, session-to-lead rate, lead-to-MQL rate, MQL-to-opp, opp-to-win, avg deal
    "Paid search":    (9000, 0.012, 0.45, 0.30, 0.25, 14000),
    "Paid social":    (8000, 0.006, 0.30, 0.22, 0.20, 11000),
    "Organic search": (12000, 0.008, 0.40, 0.28, 0.25, 15000),
    "Email":          (5000, 0.015, 0.50, 0.32, 0.28, 16000),
    "In-app message": (3000, 0.030, 0.60, 0.40, 0.35, 12000),
    "Referral":       (2000, 0.018, 0.55, 0.38, 0.30, 18000),
    "Direct":         (6000, 0.010, 0.40, 0.30, 0.25, 15000),
}
MONTHS = pd.period_range("2026-01", "2026-06", freq="M")
CHAT_SHARE = 0.30          # share of leads captured by the chat widget
ROUTED_SHARE = 0.35        # share of form leads that go through lead routing
DUPLICATE_SHARE = 0.06     # share of leads that submit a second time
BOT_SESSIONS = 0.35        # extra paid social sessions that are bots, as a share of real ones

sessions, leads, funnel, truth = [], [], [], []
sid = lid = vid = 0
for month in MONTHS:
    start = month.start_time
    for ch, (n_month, s2l, l2m, m2o, o2w, deal) in CHANNELS.items():
        n = int(rng.poisson(n_month))
        for _ in range(n):
            sid += 1; vid += 1
            ts = start + pd.Timedelta(seconds=int(rng.integers(0, month.days_in_month * 86400)))
            dur = int(rng.gamma(2.0, 60)); pages = int(1 + rng.poisson(2.2))
            sessions.append((sid, vid, ts, ch, dur, pages, 0))
            if rng.random() >= s2l:
                continue
            # A lead is created from this session.
            lid += 1
            email = f"person{lid}@example-co{rng.integers(1, 4000)}.com"
            via = "chat" if rng.random() < CHAT_SHARE else "form"
            form = "In-app request form" if (ch == "In-app message" and via == "form") else "Website form" if via == "form" else "Chat widget"
            routed = via == "form" and rng.random() < ROUTED_SHARE
            if via == "chat":
                recorded = "Direct"                   # defect 1
            elif routed:
                recorded = "Sales Inbound"            # defect 2
            elif form == "In-app request form":
                recorded = ""                         # defect 3
            else:
                recorded = ch
            created = ts + pd.Timedelta(minutes=int(rng.integers(1, 30)))
            # Cookie blocking or consent opt-out: 10% of leads cannot be linked to a web visit.
            link = vid if rng.random() >= 0.10 else None
            leads.append((lid, email, link, created, via, form, routed, recorded))
            truth.append((lid, ch))
            mql = rng.random() < l2m
            opp = mql and rng.random() < m2o
            won = opp and rng.random() < o2w
            amount = round(float(rng.gamma(4.0, deal / 4.0)), -2) if opp else 0.0
            funnel.append((lid, mql, opp, won, amount))
            if rng.random() < DUPLICATE_SHARE:          # defect 4: same person submits again
                lid += 1
                leads.append((lid, email, link, created + pd.Timedelta(hours=int(rng.integers(1, 72))),
                              via, form, routed, recorded))
                truth.append((lid, ch))
                funnel.append((lid, mql, False, False, 0.0))   # duplicate never becomes the opportunity
        if ch == "Paid social":                          # defect 5: bot clicks
            for _ in range(int(n * BOT_SESSIONS)):
                sid += 1; vid += 1
                ts = start + pd.Timedelta(seconds=int(rng.integers(0, month.days_in_month * 86400)))
                sessions.append((sid, vid, ts, ch, int(rng.integers(0, 3)), 1, 1))

ws = pd.DataFrame(sessions, columns=["session_id", "visitor_id", "session_start", "channel",
                                     "duration_sec", "pages_viewed", "_is_bot"])
ws.drop(columns="_is_bot").to_csv(OUT / "web_sessions.csv", index=False)
ws[["session_id", "_is_bot"]].to_csv(OUT / "_truth_bots.csv", index=False)
pd.DataFrame(leads, columns=["lead_id", "email", "visitor_id", "created_at", "captured_via", "form_name",
                             "passed_routing", "lead_source"]).to_csv(OUT / "crm_leads.csv", index=False)
pd.DataFrame(funnel, columns=["lead_id", "is_mql", "is_opportunity", "is_won", "pipeline_amount"]
             ).to_csv(OUT / "crm_funnel.csv", index=False)
pd.DataFrame(truth, columns=["lead_id", "true_channel"]).to_csv(OUT / "_truth_leads.csv", index=False)
print(f"{len(ws):,} sessions, {len(leads):,} lead records, {sum(f[2] for f in funnel):,} opportunities")

import os
import requests
import streamlit as st
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh
from cold_fronts import get_cold_fronts

# 1. Page Configuration
st.set_page_config(page_title="+EV BOOKIE", page_icon="📉", layout="wide")

# 2. FULL CSS (UNCHANGED)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #060912 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #e2e8f0;
}

[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Live scores ticker ── */
.scores-bar {
    background: #020408;
    border-bottom: 1px solid #1e293b;
    padding: 12px 0;
    overflow: hidden;
    white-space: nowrap;
}
.scores-track {
    display: inline-flex;
    animation: scroll-left 120s linear infinite;
}
@keyframes scroll-left {
    0% { transform:translateX(0); }
    100% { transform:translateX(-50%); }
}
.score-chip {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin: 0 30px;
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
}

/* ── Brand Header ── */
.pv-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1000px;
    margin: 40px auto 30px;
    padding: 0 20px;
}
.pv-logo-name {
    font-size: 42px;
    font-weight: 900;
    background: linear-gradient(90deg, #f87171 0%, #ffffff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1.5px;
}
.pv-beer-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #0f172a;
    border: 1.5px solid #1e293b;
    border-radius: 100px;
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 700;
    color: #7dd3fc;
    text-decoration: none;
}

/* ── Stats Row ── */
.pv-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    max-width: 1000px;
    margin: 0 auto 30px;
    padding: 0 20px;
}
.pv-stat {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 20px;
    padding: 22px;
    text-align: center;
}
.pv-stat-num {
    font-size: 38px;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 6px;
    color: #f87171;
}
.pv-stat-lbl {
    font-size: 11px;
    text-transform: uppercase;
    color: #475569;
    letter-spacing: 1.5px;
}

/* ── Cards ── */
.card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid #1e293b;
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

@media (max-width: 768px) {
    .pv-header {
        flex-direction: column;
        gap: 12px;
        text-align: center;
    }

    .pv-logo-name {
        font-size: 28px !important;
    }

    .pv-stats {
        grid-template-columns: 1fr !important;
        gap: 10px;
    }

    .pv-stat {
        padding: 16px !important;
    }

    .pv-stat-num {
        font-size: 28px !important;
    }

    .card {
        padding: 18px !important;
    }

    .score-chip {
        font-size: 11px !important;
        margin: 0 12px !important;
    }

    .pv-beer-btn {
        padding: 8px 16px !important;
        font-size: 12px !important;
    }
}

# 3. CACHE
@st.cache_data(ttl=1800)
def get_cached_bets(_key):
    return find_ev_bets(_key)

@st.cache_data(ttl=300)
def fetch_scores():
    scores = []
    try:
        for league in ["mlb", "nba"]:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/"
                f"{'baseball' if league=='mlb' else 'basketball'}/{league}/scoreboard",
                timeout=5
            )
            if r.status_code == 200:
                for event in r.json().get("events", []):
                    comp = event["competitions"][0]
                    t = comp["competitors"]
                    home = next(x for x in t if x["homeAway"] == "home")
                    away = next(x for x in t if x["homeAway"] == "away")

                    scores.append({
                        "league": league.upper(),
                        "away": away["team"]["abbreviation"],
                        "home": home["team"]["abbreviation"],
                        "a_score": away.get("score", ""),
                        "h_score": home.get("score", ""),
                        "status": event["status"]["type"]["shortDetail"]
                    })
    except:
        pass
    return scores

st_autorefresh(interval=1800000, key="refresh_tick")

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
api_key = os.environ.get("ODDS_API_KEY", "")
bets, _ = get_cached_bets(api_key)

# ❄️ COLD FRONTS (FIXED SAFELY)
cold_fronts = []
ticker_display = "No Cold Fronts Today"

try:
    cold_fronts = get_cold_fronts()

    if cold_fronts:
        ticker_display = " • ".join([
            f"{p['name']} [K/9:{p['k9']}] ❄️{p['cold_score']}"
            for p in cold_fronts[:10]
        ])
except:
    ticker_display = "Cold Fronts Error"

# ─────────────────────────────────────────────
# SCORES TICKER
# ─────────────────────────────────────────────
scores = fetch_scores()

if scores:
    chips = "".join([
        f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} '
        f'<span style="color:#475569;margin-left:5px;">{s["status"]}</span></span>'
        for s in scores
    ])

    st.markdown(
        f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# HEADER (UNCHANGED)
# ─────────────────────────────────────────────
st.markdown("""
<div class="pv-header">
    <div>
        <div class="pv-logo-name">+EV BOOKIE</div>
        <div style="color:#fff;font-size:11px;font-weight:800;letter-spacing:1px;">
            +EV ANALYTICS ENGINE • Bet on the chaos, not the perfection.
        </div>
    </div>
    <a href="https://buymeacoffee.com/notjxck" class="pv-beer-btn" target="_blank">🍺 Support Chaos</a>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────
num_edges = len(bets) if bets else 0
avg_val = (sum(b.get("EV %", 0) for b in bets) / num_edges) if num_edges else 0
top_val = max((b.get("EV %", 0) for b in bets), default=0)

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{num_edges}</div><div class="pv-stat-lbl">Live Edges</div></div>
    <div class="pv-stat"><div class="pv-stat-num">{avg_val:.1f}%</div><div class="pv-stat-lbl">Avg +EV</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{top_val:.1f}%</div><div class="pv-stat-lbl">Highest EV</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="max-width:1000px; margin: 0 auto 30px; padding: 0 20px;">
    <div class="card" style="border-left: 4px solid #f87171;">
        <h3 style="color:#f87171; margin:0 0 10px 0; font-size:18px; font-weight:900;">
            📉 The "Anti-Public" Strategy
        </h3>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:0;">
            The Public bets on records and highlight reels. We bet on <span style="color: #f87171; font-weight: 800;">Regression to the Mean</span>. 
            When the hype peaks, we short the outcome. Market crashes don't happen to us: we profit from them.
            <span style="color:#ffffff; font-style:italic;">1929 Style: BET THE UNDER.</span>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ❄️ COLD FRONTS (UNDER STATS — FIXED LOCATION)
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="max-width:1000px;margin:0 auto 20px;padding:0 20px;">
    <div class="card" style="border-left:4px solid #38bdf8;">
        <h3 style="color:#38bdf8;margin:0 0 10px 0;font-size:16px;font-weight:900;">
            ❄️ COLD FRONTS (STRIKEOUT DEVIATION)
        </h3>
        <div style="color:#94a3b8;font-size:13px;font-family:monospace;">
            {ticker_display}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# EV FEED (UNCHANGED)
# ─────────────────────────────────────────────
if bets:
    bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)

    for b in bets:
        st.markdown(f"""
        <div class="card">
            <div style="font-size:22px;font-weight:900;color:white;">{b.get("Player")}</div>
            <div style="color:#94a3b8;">{b.get("Game")}</div>
            <div style="color:#fbbf24;font-size:26px;font-weight:800;margin-top:8px;">
                +{b.get("EV %")}% EV
            </div>
        </div>
        """, unsafe_allow_html=True)

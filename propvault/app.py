import os
import requests
import streamlit as st
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="+EV BOOKIE", page_icon="📉", layout="wide")

# 2. FULL CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #060912 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #e2e8f0;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stStatusWidget"] { display: none !important; }

.block-container,
[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"],
section[data-testid="stMain"] > div {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Live scores ticker ── */
.scores-bar {
    background: #020408;
    border-bottom: 1px solid #1e293b;
    padding: 12px 0;
    overflow: hidden;
    white-space: nowrap;
    width: 100%;
}
.scores-track {
    display: inline-flex;
    animation: scroll-left 180s linear infinite;
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

/* ── Centered wrapper ── */
.pv-wrap {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 24px;
}

/* ── Brand Header ── */
.pv-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 40px 0 30px;
}

.pv-logo-name {
    font-size: 42px;
    font-weight: 900;
    background: linear-gradient(90deg, #38cdff 0%, #ffffff 100%);
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
    color: #38cdff;
    text-decoration: none;
}

/* ── Stats Row ── */
.pv-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;
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
    color: #38cdff;
}

.pv-stat-lbl {
    font-size: 11px;
    text-transform: uppercase;
    color: #cbd5e1;
    letter-spacing: 1.5px;
}

/* ── Cards & Badges ── */
.card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid #1e293b;
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 16px;
}

.strategy-badge {
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 12px;
}

.under-theme { background: #064e3b; color: #34d399; }
.over-theme { background: #450a0a; color: #f87171; }

/* ── Kelly container ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid #1e293b !important;
    border-radius: 24px !important;
    padding: 28px !important;
    max-width: 852px !important;
    width: 100% !important;
    margin: 0 auto 24px !important;
    box-sizing: border-box !important;
}

[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] > div > div {
    padding-bottom: 0 !important;
}

/* 🔥 Clean bankroll input (replaces number_input entirely) */
input[type="text"] {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    width: 100% !important;
}

/* 🔥 Clean number input (no +/- buttons, perfectly centered) */

/* Container alignment fix */
[data-testid="stNumberInput"] > div {
    display: flex;
    align-items: center;
    width: 100%;
}

/* Input styling */
[data-testid="stNumberInput"] input {
    width: 100% !important;
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
}

/* ❌ Remove ugly +/- stepper */
[data-testid="stNumberInput"] button {
    display: none !important;
}

@media (max-width: 600px) {
    .pv-header { flex-direction: column; gap: 12px; }
    .pv-logo-name { font-size: 32px; }
    .pv-stats { grid-template-columns: 1fr; gap: 10px; }
    .pv-stat-num { font-size: 28px; }
    .card { flex-direction: column; align-items: flex-start !important; gap: 12px; }
    .strategy-badge { font-size: 14px !important; padding: 4px 10px !important; }
}
</style>
""", unsafe_allow_html=True)

# 3. Cache Functions

@st.cache_data(ttl=1800)
def get_cached_bets(bankroll: float = 100.0):
    api_key = os.environ.get("ODDS_API_KEY", "")
    return find_ev_bets(api_key, bankroll)

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

# Auto-refresh
st_autorefresh(interval=1800000, key="refresh_tick")

# ── RENDER ──

# 1. Scores Ticker
scores = fetch_scores()
if scores:
    chips = "".join([
        f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} '
        f'<span style="color:#cbd5e1; margin-left:5px;">{s["status"]}</span></span>'
        for s in scores
    ])
    st.markdown(
        f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>',
        unsafe_allow_html=True
    )

# 2. Header
st.markdown("""
<div class="pv-wrap">
    <div class="pv-header">
        <div>
            <div class="pv-logo-name">+EV BOOKIE</div>
            <div style="color: #ffffff; font-size: 11px; font-weight: 800; letter-spacing: 1px;">
                +EV ANALYTICS ENGINE <span style="color: #f87171; margin-left:10px;">• Bet on the chaos, not the perfection.</span>
            </div>
        </div>
        <a href="https://buymeacoffee.com/notjxck" class="pv-beer-btn" target="_blank">
            <span>🍺</span> Support The Servers
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Load bets for stats
bets, _ = get_cached_bets(100.0)

num_edges = len(bets) if bets else 0
avg_val = (sum(b.get('EV %', 0) for b in bets) / num_edges) if num_edges > 0 else 0
top_val = max([b.get('EV %', 0) for b in bets], default=0)

st.markdown(f"""
<div class="pv-wrap">
    <div class="pv-stats">
        <div class="pv-stat"><div class="pv-stat-num">{num_edges}</div><div class="pv-stat-lbl">Edges Found</div></div>
        <div class="pv-stat"><div class="pv-stat-num">{avg_val:.1f}%</div><div class="pv-stat-lbl">Avg +EV</div></div>
        <div class="pv-stat"><div class="pv-stat-num">+{top_val:.1f}%</div><div class="pv-stat-lbl">Highest Edge</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Kelly Calculator
with st.container(border=True):
    st.markdown("""
        <h3 style="color:#38cdff; margin:0 0 6px 0; font-size:18px; font-weight:900;">
            📊 Kelly Bankroll Calculator
        </h3>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:0 0 4px 0;">
            Enter your available <span style="color:#ffffff; font-weight:800;">Novig balance</span> to see half-Kelly suggested bet sizes on each edge below.
        </p>
    """, unsafe_allow_html=True)

    bankroll_input = st.text_input(
        "Available Bankroll ($)",
        value="100.00"
    )

    # 🔥 Safe parsing (prevents crashes)
    try:
        bankroll = float(bankroll_input.replace(",", ""))
    except:
        bankroll = 0.0

# Reload bets with actual bankroll
bets, _ = get_cached_bets(bankroll)

# 5. The Feed
if bets:
    sorted_bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)
    feed_html = []

    for i, b in enumerate(sorted_bets):
        b_side_full = b.get('Side', 'Under 0.0')
        b_target_odds = b.get('Target Odds', '-')
        b_fair_odds = b.get('Fair Odds', '-')
        b_l5 = b.get('L5')
        b_kelly = b.get('Kelly (Half)', '$0.00')

        b_theme = "under-theme" if "Under" in b_side_full else "over-theme"
        l5_display = f'<div style="color:#7dd3fc; font-size:13px; font-weight:800; margin: 8px 0;">{b_l5}</div>' if b_l5 else ""

        comparison_bar = f"""
        <div style="display: flex; gap: 20px; margin-top: 12px; border-top: 1px solid #1e293b; padding-top: 10px; flex-wrap: wrap;">
            <div style="font-size: 16px; color: #cbd5e1; font-weight:700;">NOVIG LINE: <span style="color: #38cdff;">{b_target_odds}</span></div>
            <div style="font-size: 16px; color: #cbd5e1; font-weight:700;">PINNACLE (SHARP): <span style="color: #f8fafc;">{b_fair_odds}</span></div>
            <div style="font-size: 16px; color: #cbd5e1; font-weight:700;">HALF KELLY: <span style="color: #34d399;">{b_kelly}</span></div>
        </div>
        """

        if i == 0:
            card = f'<div class="card" style="border: 1px solid #f87171; position: relative; overflow: hidden;">' \
                   f'<div style="position: absolute; right: -10px; top: -10px; font-size: 100px; opacity: 0.10;">📉</div>' \
                   f'<div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; position: relative; z-index:1;">' \
                   f'<div><div class="strategy-badge under-theme" style="margin-bottom: 12px; display: inline-block;">🎯 BEST UNDER</div>' \
                   f'<div style="font-size: 42px; font-weight: 900; line-height: 1;">{b.get("Player")}</div>' \
                   f'<div style="color: #cbd5e1; font-size: 16px; margin: 5px 0;">{b.get("Game")}</div>' \
                   f'{l5_display}' \
                   f'<span class="strategy-badge {b_theme}" style="font-size: 18px; padding: 6px 12px;">{b_side_full.upper()}</span></div>' \
                   f'<div style="text-align: right;"><div style="color: #38cdff; font-size: 64px; font-weight: 900;">+{b.get("EV %")}%</div>' \
                   f'<div style="font-size: 11px; color: #cbd5e1; font-weight: 800;">EV Percentage</div></div></div>' \
                   f'{comparison_bar}</div>'
        else:
            card = f'<div class="card">' \
                   f'<div style="display:flex; flex-wrap: wrap; justify-content:space-between; align-items:center;">' \
                   f'<div><div style="font-size:24px; font-weight:900;">{b.get("Player")} <span class="strategy-badge {b_theme}" style="margin-left:10px;">{b_side_full.upper()}</span></div>' \
                   f'<div style="color: #38cdff; font-size: 14px;">{b.get("Game")}</div>' \
                   f'{l5_display}</div>' \
                   f'<div style="color:#38cdff; font-size:38px; font-weight:900;">+{b.get("EV %")}%</div></div>' \
                   f'{comparison_bar}</div>'

        feed_html.append(card)

    st.markdown(f'<div class="pv-wrap">{"".join(feed_html)}</div>', unsafe_allow_html=True)

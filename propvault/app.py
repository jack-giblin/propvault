import os
import requests
import streamlit as st
import textwrap
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

@media (max-width: 600px) {
    .pv-header {
        flex-direction: column;
        gap: 12px;
    }
    .pv-logo-name {
        font-size: 32px;
    }
    .pv-stats {
        grid-template-columns: 1fr;
        gap: 10px;
    }
    .pv-stat-num {
        font-size: 28px;
    }
    .card {
        flex-direction: column;
        align-items: flex-start !important;
        gap: 12px;
    }
    .strategy-badge {
        font-size: 14px !important;
        padding: 4px 10px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# 3. API Logic with 30-Minute Credit Protection

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


# Auto-refresh UI
st_autorefresh(interval=1800000, key="refresh_tick")

# 4. Bankroll Input (before cache call so it feeds Kelly)
st.markdown("""
<div style="max-width:1000px; margin: 30px auto 0; padding: 0 20px;">
    <div class="card">
        <h3 style="color:#38cdff; margin:0 0 10px 0; font-size:18px; font-weight:900;">
            📊 Kelly Bankroll Calculator
        </h3>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:0 0 4px 0;">
            Enter your available <span style="color:#ffffff; font-weight:800;">Novig balance</span> to see half-Kelly suggested bet sizes on each edge below.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    bankroll = st.number_input(
        "Available Bankroll ($)",
        min_value=10.0,
        max_value=100000.0,
        value=100.0,
        step=10.0,
        format="%.2f",
    )

# Load cached data
bets, _ = get_cached_bets(bankroll)

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
st.markdown(f"""
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
""", unsafe_allow_html=True)

# 3. Stats Row
num_edges = len(bets) if bets else 0
avg_val = (sum(b.get('EV %', 0) for b in bets) / num_edges) if num_edges > 0 else 0
top_val = max([b.get('EV %', 0) for b in bets], default=0)

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{num_edges}</div><div class="pv-stat-lbl">Edges Found</div></div>
    <div class="pv-stat"><div class="pv-stat-num">{avg_val:.1f}%</div><div class="pv-stat-lbl">Avg +EV</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{top_val:.1f}%</div><div class="pv-stat-lbl">Highest Edge</div></div>
</div>
""", unsafe_allow_html=True)

# 4. Strategy Guide
st.markdown("""
<style>
@keyframes pulse {
    0% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.05); }
    100% { opacity: 0.6; transform: scale(1); }
}

@keyframes glow {
    0% { box-shadow: 0 0 5px rgba(248,113,113,0.2); }
    50% { box-shadow: 0 0 18px rgba(248,113,113,0.6); }
    100% { box-shadow: 0 0 5px rgba(248,113,113,0.2); }
}

.under-badge {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:4px 10px;
    border-radius:999px;
    background: rgba(248,113,113,0.15);
    color:#f87171;
    font-size:12px;
    font-weight:800;
    animation: pulse 1.8s infinite;
}

.card-animated {
    border-left: 4px solid #f87171;
    animation: glow 2.5s infinite;
}
</style>
<div style="max-width:1000px; margin: 0 auto 30px; padding: 0 20px;">
    <div class="card card-animated">
        <h3 style="color:#f87171; margin:0 0 10px 0; font-size:18px; font-weight:900;">
            📉 The "Anti-Public" Strategy
        </h3>
        <div class="under-badge">
            <span>📡</span>
            UNDER MODE ACTIVE
        </div>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:12px 0;">
            We specialize in <span style="color:#ffffff; font-weight:800;">UNDER bets only</span>.
            When public perception inflates totals and player lines, markets drift above true expectation.
            We target the correction phase — where <span style="color:#f87171; font-weight:800;">regression restores balance</span>.
        </p>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:0 0 10px 0;">
            Every bet must pass strict filters:
        </p>
        <ul style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:0 0 12px 18px;">
            <li>EV between <span style="color:#ffffff; font-weight:800;">1.5% and 8%</span></li>
            <li>Minimum <span style="color:#ffffff; font-weight:800;">40% win probability</span></li>
            <li>Only <span style="color:#f87171; font-weight:800;">under outcomes</span></li>
        </ul>
        <p style="color:#ffffff; font-size:14px; line-height:1.7; margin:0; font-style:italic;">
            No noise. No hype. Only mispriced downside.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

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

    st.markdown(f'<div style="max-width:1000px; margin:0 auto; padding:0 20px;">{"".join(feed_html)}</div>', unsafe_allow_html=True)

"""
PropVault — +EV Engine
Railway deployment. Run: streamlit run app.py
"""

import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets

# 1. Page Configuration
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# 2. CSS Overhaul (Restores Header, Slows Ticker, Adds Odds Styling)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap');

/* Main Body & Layout */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #060912 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #e2e8f0;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Live scores ticker (Slowed to 120s for readability) ── */
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
.scores-track:hover { animation-play-state: paused; }
@keyframes scroll-left { 0% { transform:translateX(0); } 100% { transform:translateX(-50%); } }

.score-chip {
    display: inline-flex; align-items: center; gap: 10px;
    margin: 0 30px;
    font-size: 13px; font-weight: 700; color: #94a3b8;
}

/* ── Brand Header ── */
.pv-header {
    display: flex; align-items: center; justify-content: space-between;
    max-width: 1000px; margin: 40px auto 30px; padding: 0 20px;
}
.pv-logo { display: flex; align-items: center; gap: 18px; }
.pv-logo-name {
    font-size: 42px; font-weight: 900;
    background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -1.5px;
}
.pv-beer-btn {
    display: flex; align-items: center; gap: 8px;
    background: #0f172a; border: 1.5px solid #1e293b;
    border-radius: 100px; padding: 10px 22px;
    font-size: 14px; font-weight: 700; color: #7dd3fc;
    text-decoration: none; transition: 0.2s;
}
.pv-beer-btn:hover { border-color: #7dd3fc; background: #1e293b; color: #fff; }

/* ── Stats Row ── */
.pv-stats {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 16px; max-width: 1000px; margin: 0 auto 30px; padding: 0 20px;
}
.pv-stat {
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 20px; padding: 22px; text-align: center;
}
.pv-stat-num { font-size: 38px; font-weight: 900; line-height: 1; margin-bottom: 6px; }
.pv-stat-lbl { font-size: 11px; text-transform: uppercase; color: #475569; letter-spacing: 1.5px; }

/* ── Strategy Card ── */
.card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid #1e293b;
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 16px;
}
.strategy-box { border-left: 4px solid #ef4444; }
.s-stat-under { background: #064e3b; color: #34d399; padding: 2px 8px; border-radius: 6px; font-weight: 800; }
.s-stat-over { background: #450a0a; color: #f87171; padding: 2px 8px; border-radius: 6px; font-weight: 800; }

/* ── Bet Cards with Odds Badges ── */
.odds-row { display: flex; align-items: center; gap: 12px; margin-top: 15px; }
.odds-badge {
    background: #052e16; color: #4ade80; border: 1px solid #064e3b;
    padding: 6px 14px; border-radius: 10px; font-weight: 900; font-size: 18px;
}
.fair-label { color: #475569; font-size: 13px; font-weight: 600; }

/* ── Hunt Button ── */
div.stButton > button {
    width: 100% !important; max-width: 400px; height: 64px !important;
    background: #0f172a !important; border: 2px solid #38bdf8 !important;
    border-radius: 100px !important; color: #38bdf8 !important;
    font-weight: 900 !important; font-size: 17px !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    margin: 20px auto !important; display: block;
}
div.stButton > button:hover {
    background: #111d35 !important;
    box-shadow: 0 0 28px rgba(56, 189, 248, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# 3. Live Scores Fetch (ESPN API)
@st.cache_data(ttl=120)
def fetch_scores():
    scores = []
    try:
        for league in ["mlb", "nba"]:
            sport_type = 'baseball' if league == 'mlb' else 'basketball'
            r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{sport_type}/{league}/scoreboard", timeout=5)
            if r.status_code == 200:
                for event in r.json().get("events", []):
                    comp = event["competitions"][0]
                    teams = comp["competitors"]
                    home = next(t for t in teams if t["homeAway"] == "home")
                    away = next(t for t in teams if t["homeAway"] == "away")
                    scores.append({
                        "league": league.upper(),
                        "away": away["team"]["abbreviation"],
                        "home": home["team"]["abbreviation"],
                        "a_score": away.get("score", ""),
                        "h_score": home.get("score", ""),
                        "status": event["status"]["type"]["shortDetail"]
                    })
    except: pass
    return scores

# 4. EV Data Management
api_key = os.environ.get("ODDS_API_KEY", "")
CACHE_TIME = 300

if "bets" not in st.session_state: st.session_state.bets = []
if "fetched_at" not in st.session_state: st.session_state.fetched_at = 0

def update_data():
    if not api_key:
        st.error("ODDS_API_KEY not found in environment variables.")
        return
    # find_ev_bets should return list of dicts with keys: 
    # ['Sport', 'Game', 'Market', 'Side', 'Target Odds', 'Fair Odds', 'EV %']
    bets, errors = find_ev_bets(api_key)
    st.session_state.bets = bets
    st.session_state.fetched_at = time.time()

if (time.time() - st.session_state.fetched_at) >= CACHE_TIME:
    update_data()

# ── RENDER START ──

# 1. Ticker
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span style="color:#1e293b; margin-left:5px;">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# 2. Hero Header
st.markdown(f"""
<div class="pv-header">
    <div class="pv-logo">
        <div>
            <div class="pv-logo-name">PropVault</div>
            <div style="color:#475569; font-size:14px; font-weight:500;">When the "Fair Value" price is lower than the available odds, you have a mathematical edge.</div>
        </div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <a class="pv-beer-btn" href="https://www.buymeacoffee.com/notjxck" target="_blank">🍺 Buy me a beer</a>
        <div style="color:#22c55e; border:1px solid #166534; background:#052e16; padding:8px 20px; border-radius:100px; font-size:12px; font-weight:900; letter-spacing:1px;">● LIVE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Analytics Row
bets = st.session_state.bets
avg_ev = round(sum(b["EV %"] for b in bets)/len(bets), 1) if bets else 0
top_ev = max([b["EV %"] for b in bets]) if bets else 0

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num" style="color:#f8fafc;">{len(bets)}</div><div class="pv-stat-lbl">Edges Found</div></div>
    <div class="pv-stat"><div class="pv-stat-num" style="color:#7dd3fc;">+{avg_ev}%</div><div class="pv-stat-lbl">Avg EV</div></div>
    <div class="pv-stat"><div class="pv-stat-num" style="color:#fbbf24;">+{top_ev}%</div><div class="pv-stat-lbl">Top EV</div></div>
</div>
""", unsafe_allow_html=True)

# 4. Main Content Wrapper
st.markdown('<div style="max-width:1000px; margin: 0 auto; padding: 0 20px;">', unsafe_allow_html=True)

# Anti-Public Strategy Card
st.markdown("""
<div class="card strategy-box">
    <h3 style="color:#ef4444; margin:0 0 10px 0; font-size:18px; font-weight:900;">📉 The "Anti-Public" Strategy</h3>
    <p style="color:#94a3b8; font-size:14px; line-height:1.7; margin:0;">
        Data confirms: <span class="s-stat-over">Overs return -2.26% ROI</span> while 
        <span class="s-stat-under">Unders return +3.33% ROI</span>.
        An <b>Over</b> almost always requires flawless play. 
        An <b>Under</b> wins if there is an injury, blowout, foul trouble, or just a bad night. 
        <i>Bet on the chaos, not the perfection.</i>
    </p>
</div>
""", unsafe_allow_html=True)

# Hunt/Refresh Button
if st.button("🦄 HUNT FOR UNICORNS"):
    with st.spinner("Scanning Spreads & Totals..."):
        update_data()
    st.rerun()

# Bet Card List
if bets:
    st.markdown('<p style="color:#475569; font-weight:800; font-size:11px; letter-spacing:2px; margin:30px 0 15px 0; text-transform:uppercase;">Live Game Edges</p>', unsafe_allow_html=True)
    for b in bets:
        # Style based on EV strength
        tier_color = "#7dd3fc" if b["EV %"] >= 7 else "#fbbf24" if b["EV %"] >= 5 else "#64748b"
        
        st.markdown(f"""
        <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
            <div style="flex:1;">
                <div style="color:{tier_color}; font-size:10px; font-weight:800; letter-spacing:1px; margin-bottom:6px; text-transform:uppercase;">
                    {b.get('Sport', 'SPORT')} · {b.get('Market', 'MARKET')}
                </div>
                <div style="font-size:24px; font-weight:900; color:#fff; margin-bottom:4px; letter-spacing:-0.5px;">
                    {b.get('Side', 'Unknown')}
                </div>
                <div style="color:#64748b; font-size:14px; font-weight:500;">
                    {b.get('Game', 'Game Details')}
                </div>
                <div class="odds-row">
                    <span class="odds-badge">{b.get('Target Odds', 'N/A')}</span>
                    <span class="fair-label">Fair: {b.get('Fair Odds', 'N/A')}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:{tier_color}; font-size:38px; font-weight:900; letter-spacing:-2px; line-height:1;">
                    +{b.get('EV %', 0)}%
                </div>
                <div style="color:#334155; font-size:10px; font-weight:800; text-transform:uppercase; margin-top:5px; letter-spacing:1px;">
                    Expected Value
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; padding:60px 0; color:#1e293b;">
        <div style="font-size:40px; margin-bottom:10px;">📊</div>
        <div style="font-size:16px; font-weight:700;">No edges found for Spreads or Totals right now.</div>
        <div style="font-size:13px;">Markets are currently tight. Refresh in a few minutes.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

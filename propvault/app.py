import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets

# 1. Page Configuration
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# 2. CSS & UI Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #060912 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #e2e8f0;
}

[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
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
    animation: scroll-left 100s linear infinite;
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
}
.pv-logo-sub { font-size: 14px; color: #475569; font-weight: 500; }

/* ── Glass Cards ── */
.card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid #1e293b;
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 16px;
}

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

/* ── Strategy Styling ── */
.strategy-box { border-left: 4px solid #ef4444; }
.s-stat-under { background: #064e3b; color: #34d399; padding: 2px 8px; border-radius: 6px; font-weight: 800; }
.s-stat-over { background: #450a0a; color: #f87171; padding: 2px 8px; border-radius: 6px; font-weight: 800; }

/* ── Buttons ── */
div.stButton > button {
    width: 100% !important; max-width: 400px; height: 60px !important;
    background: #0f172a !important; border: 2px solid #38bdf8 !important;
    border-radius: 100px !important; color: #38bdf8 !important;
    font-weight: 800 !important; font-size: 16px !important;
    letter-spacing: 2px !important; margin: 20px auto !important; display: block;
}
</style>
""", unsafe_allow_html=True)

# 3. Live Scores Logic
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

# 4. EV Data Logic
api_key = os.environ.get("ODDS_API_KEY", "")
CACHE_TIME = 300

if "bets" not in st.session_state: st.session_state.bets = []
if "fetched_at" not in st.session_state: st.session_state.fetched_at = 0

def update_data():
    if api_key:
        bets, _ = find_ev_bets(api_key)
        st.session_state.bets = bets
        st.session_state.fetched_at = time.time()

if (time.time() - st.session_state.fetched_at) > CACHE_TIME:
    update_data()

# ── RENDER ──

# Ticker
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span style="color:#334155">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="pv-header">
    <div class="pv-logo">
        <div class="pv-logo-name">PropVault</div>
        <div class="pv-logo-sub">Novig vs Pinnacle · Edge Finder</div>
    </div>
    <div style="color:#22c55e; border:1px solid #166534; background:#052e16; padding:8px 20px; border-radius:100px; font-size:12px; font-weight:900;">● LIVE</div>
</div>
""", unsafe_allow_html=True)

# Stats Row
bets = st.session_state.bets
avg_ev = round(sum(b["EV %"] for b in bets)/len(bets), 1) if bets else 0
top_ev = max([b["EV %"] for b in bets]) if bets else 0

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{len(bets)}</div><div class="pv-stat-lbl">Edges Found</div></div>
    <div class="pv-stat"><div class="pv-stat-num" style="color:#7dd3fc">+{avg_ev}%</div><div class="pv-stat-lbl">Avg EV</div></div>
    <div class="pv-stat"><div class="pv-stat-num" style="color:#fbbf24">+{top_ev}%</div><div class="pv-stat-lbl">Top EV</div></div>
</div>
""", unsafe_allow_html=True)

# Content Container
st.markdown('<div style="max-width:1000px; margin: 0 auto; padding: 0 20px;">', unsafe_allow_html=True)

# Strategy Card
st.markdown("""
<div class="card strategy-box">
    <h3 style="color:#ef4444; margin:0 0 10px 0; font-size:18px;">📉 The "Anti-Public" Strategy</h3>
    <p style="color:#94a3b8; font-size:14px; line-height:1.6; margin:0;">
        Markets are biased. <span class="s-stat-over">Overs returned -2.26% ROI</span> while 
        <span class="s-stat-under">Unders returned +3.33% ROI</span>. PropVault prioritizes high-win-probability 
        discrepancies where the math beats the crowd.
    </p>
</div>
""", unsafe_allow_html=True)

# Hunt Button
if st.button("🦄 HUNT FOR UNICORNS"):
    update_data()
    st.rerun()

# Bet Cards
if bets:
    st.markdown('<p style="color:#475569; font-weight:800; font-size:11px; letter-spacing:2px; margin:30px 0 15px 0;">LIVE EDGES</p>', unsafe_allow_html=True)
    for b in bets:
        tier_color = "#7dd3fc" if b["EV %"] >= 7 else "#fbbf24" if b["EV %"] >= 5 else "#64748b"
        st.markdown(f"""
        <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:{tier_color}; font-size:10px; font-weight:800; letter-spacing:1px; margin-bottom:4px;">{b['Sport']}</div>
                <div style="font-size:22px; font-weight:900;">{b['Side']}</div>
                <div style="color:#64748b; font-size:13px; font-weight:500;">{b['Game']} · {b['Market']}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:{tier_color}; font-size:36px; font-weight:900; letter-spacing:-1px;">+{b['EV %']}%</div>
                <div style="color:#334155; font-size:10px; font-weight:800;">EXPECTED VALUE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center; color:#334155; padding:50px 0;">No edges currently found. Refreshing...</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

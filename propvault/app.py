import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets

# 1. Page Configuration
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# 2. CSS UI Styling (Contrast Boost)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #060912 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #f8fafc; /* Brighter default text */
}

[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Live scores ticker ── */
.scores-bar {
    background: #000000;
    border-bottom: 1px solid #1e293b;
    padding: 14px 0;
    overflow: hidden;
}
.scores-track {
    display: inline-flex;
    animation: scroll-left 120s linear infinite;
}
@keyframes scroll-left { 0% { transform:translateX(0); } 100% { transform:translateX(-50%); } }

.score-chip {
    display: inline-flex; align-items: center; gap: 10px;
    margin: 0 30px;
    font-size: 13px; font-weight: 800; 
    color: #ffffff !important;
}
/* FIX: High contrast for ticker dates/time */
.score-status {
    color: #f1f5f9 !important; 
    background: #1e293b;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 8px;
    font-weight: 700;
}

/* ── Brand Header ── */
.pv-header {
    display: flex; align-items: center; justify-content: space-between;
    max-width: 1000px; margin: 40px auto 30px; padding: 0 20px;
}
.pv-logo-container { display: flex; align-items: center; gap: 15px; }
.pv-unicorn { font-size: 45px; }
.pv-logo-name {
    font-size: 42px; font-weight: 900;
    background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -1.5px;
}
/* FIX: Readable sub-header text */
.pv-sub-header { color: #cbd5e1; font-size: 15px; font-weight: 600; margin-top: 4px; }

.pv-beer-btn {
    display: flex; align-items: center; gap: 8px;
    background: #0f172a; border: 1.5px solid #334155;
    border-radius: 100px; padding: 10px 22px;
    font-size: 14px; font-weight: 700; color: #7dd3fc;
    text-decoration: none; transition: 0.2s;
}

/* ── Strategy Card ── */
.card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 16px;
}
.strategy-box { border-left: 5px solid #ef4444; background: #111827; }
/* FIX: High contrast strategy text */
.strategy-text { color: #f8fafc !important; font-size: 15px; line-height: 1.6; font-weight: 500; }

.s-stat-under { background: #065f46; color: #6ee7b7; padding: 2px 8px; border-radius: 6px; font-weight: 900; }
.s-stat-over { background: #7f1d1d; color: #fca5a5; padding: 2px 8px; border-radius: 6px; font-weight: 900; }

/* ── Odds Badges ── */
.odds-badge {
    background: #064e3b; color: #6ee7b7; border: 1px solid #065f46;
    padding: 8px 16px; border-radius: 12px; font-weight: 900; font-size: 20px;
}
.fair-label { color: #94a3b8; font-size: 14px; font-weight: 700; }

/* ── Button ── */
div.stButton > button {
    width: 100% !important; max-width: 400px; height: 64px !important;
    background: #0f172a !important; border: 2px solid #38bdf8 !important;
    border-radius: 100px !important; color: #38bdf8 !important;
    font-weight: 900 !important; font-size: 17px !important;
    display: block; margin: 20px auto !important;
}
</style>
""", unsafe_allow_html=True)

# 3. Live Scores Fetch
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
                        "a_score": away.get("score", "0"),
                        "h_score": home.get("score", "0"),
                        "status": event["status"]["type"]["shortDetail"]
                    })
    except: pass
    return scores

# 4. Data Init
api_key = os.environ.get("ODDS_API_KEY", "")
if "bets" not in st.session_state: st.session_state.bets = []
if "fetched_at" not in st.session_state: st.session_state.fetched_at = 0

def update_data():
    if api_key:
        bets, _ = find_ev_bets(api_key)
        st.session_state.bets = bets
        st.session_state.fetched_at = time.time()

if (time.time() - st.session_state.fetched_at) >= 300:
    update_data()

# ── RENDER ──

# 1. Ticker
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span class="score-status">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# 2. Hero Header with Unicorn
st.markdown(f"""
<div class="pv-header">
    <div class="pv-logo-container">
        <div class="pv-unicorn">🦄</div>
        <div>
            <div class="pv-logo-name">PropVault</div>
            <div class="pv-sub-header">Sharp-Aggregated Player Prop Edges</div>
        </div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <a class="pv-beer-btn" href="https://www.buymeacoffee.com/notjxck" target="_blank">🍺 Buy me a beer</a>
        <div style="color:#4ade80; border:1px solid #065f46; background:#064e3b; padding:8px 20px; border-radius:100px; font-size:12px; font-weight:900;">● LIVE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Analytics
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

# 4. Main Body
st.markdown('<div style="max-width:1000px; margin: 0 auto; padding: 0 20px;">', unsafe_allow_html=True)

# Strategy Card
st.markdown("""
<div class="card strategy-box">
    <h3 style="color:#ef4444; margin:0 0 10px 0; font-size:20px; font-weight:900;">📉 The "Anti-Public" Strategy</h3>
    <p class="strategy-text">
        Data confirms: <span class="s-stat-over">Overs return -2.26% ROI</span> while 
        <span class="s-stat-under">Unders return +3.33% ROI</span>.<br><br>
        An <b>Over</b> requires perfection. An <b>Under</b> wins if there is an injury, blowout, foul trouble, or just a bad night. 
        <b>Bet on the chaos, not the perfection.</b>
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🦄 HUNT FOR UNICORNS"):
    update_data()
    st.rerun()

# Bet Cards
if bets:
    for b in bets:
        tier_color = "#7dd3fc" if b["EV %"] >= 7 else "#fbbf24" if b["EV %"] >= 5 else "#94a3b8"
        st.markdown(f"""
        <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
            <div style="flex:1;">
                <div style="color:{tier_color}; font-size:11px; font-weight:800; letter-spacing:1px; margin-bottom:6px; text-transform:uppercase;">
                    {b.get('Sport')} · {b.get('Market')}
                </div>
                <div style="font-size:26px; font-weight:900; color:#fff; margin-bottom:2px;">
                    {b.get('Player', 'Unknown')}
                </div>
                <div style="font-size:20px; font-weight:700; color:{tier_color}; margin-bottom:8px;">
                    {b.get('Side')}
                </div>
                <div style="color:#94a3b8; font-size:14px; font-weight:600;">{b.get('Game')}</div>
                <div class="odds-row">
                    <span class="odds-badge">{b.get('Target Odds')}</span>
                    <span class="fair-label">Fair: {b.get('Fair Odds')}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:{tier_color}; font-size:42px; font-weight:900; letter-spacing:-2px; line-height:1;">+{b.get('EV %')}%</div>
                <div style="color:#475569; font-size:10px; font-weight:800; text-transform:uppercase; margin-top:5px;">Expected Value</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center; padding:60px 0; color:#475569; font-weight:700;">Scanning for edges...</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

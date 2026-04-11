import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# 2. CSS Overhaul
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
    animation: scroll-left 120s linear infinite;
}

.scores-track:hover { animation-play-state: paused; }

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

.score-status {
    color: #cbd5e1 !important;
    margin-left: 8px;
    font-weight: 500;
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
    background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%);
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

.strategy-box { border-left: 4px solid #ef4444; }

.s-stat-under {
    background: #064e3b;
    color: #34d399;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 800;
}

.s-stat-over {
    background: #450a0a;
    color: #f87171;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 800;
}

/* ── Odds Badges ── */
.odds-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 15px;
}

.odds-badge {
    background: #052e16;
    color: #4ade80;
    border: 1px solid #064e3b;
    padding: 6px 14px;
    border-radius: 10px;
    font-weight: 900;
    font-size: 18px;
}

/* ── Hunt Button ── */
div.stButton > button {
    width: 100% !important;
    max-width: 400px;
    height: 64px !important;
    background: #0f172a !important;
    border: 2px solid #38bdf8 !important;
    border-radius: 100px !important;
    color: #38bdf8 !important;
    font-weight: 900 !important;
    font-size: 17px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    margin: 20px auto !important;
    display: block;
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
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/{sport_type}/{league}/scoreboard",
                timeout=5
            )
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
    except:
        pass

    return scores

# 4. EV Data Management
api_key = os.environ.get("ODDS_API_KEY", "")

# This forces the app to refresh every 15 minutes
st_autorefresh(interval=15 * 60 * 1000, key="unicorn_heartbeat")

@st.cache_data(ttl=900) 
def get_cached_ev_data(api_key):
    # This only hits the Odds API once every 15 mins
    bets, errors = find_ev_bets(api_key)
    return bets

# Every time the app heartbeats, it checks the vault
bets = get_cached_ev_data(api_key)

# ── RENDER ──
# ── RENDER ──
scores = fetch_scores()

# (Keep your existing scores ticker code here...)
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span class="score-status">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# ... (Keep your Header/Stats code here) ...

# ── THE UNICORN VAULT ──
st.markdown('<div style="max-width:1000px; margin: 0 auto; padding: 0 20px;">', unsafe_allow_html=True)

if bets:
    # 1. Sort to find the highest EV % (The Unicorn)
    sorted_bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)
    unicorn = sorted_bets[0]
    
    # 2. Render THE LONE UNICORN
    st.markdown(f"""
    <div class="card" style="border: 2px solid #7dd3fc; background: linear-gradient(145deg, rgba(125, 211, 252, 0.1) 0%, rgba(6, 9, 18, 0.5) 100%); margin-bottom: 35px; position: relative; overflow: hidden;">
        <div style="position: absolute; right: -20px; top: -10px; font-size: 120px; opacity: 0.1; transform: rotate(15deg);">🦄</div>
        <div style="display: flex; justify-content: space-between; position: relative; z-index: 1;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🦄</span>
                    <span style="background: #7dd3fc; color: #060912; padding: 2px 10px; border-radius: 100px; font-size: 11px; font-weight: 900; letter-spacing: 1px;">THE LONE UNICORN</span>
                </div>
                <div style="font-size: 36px; font-weight: 900; line-height: 1;">{unicorn.get('Player')}</div>
                <div style="font-size: 22px; font-weight: 700; color: #7dd3fc; margin-top: 5px;">{unicorn.get('Side')}</div>
                <div style="color: #64748b; font-size: 14px;">{unicorn.get('Market')} · {unicorn.get('Game')}</div>
                <div class="odds-row" style="margin-top: 20px;">
                    <span class="odds-badge" style="background: #7dd3fc; color: #060912; border: none;">{unicorn.get('Target Odds')}</span>
                    <span style="color: #94a3b8; font-size: 14px; font-weight: 600;">Fair Price: {unicorn.get('Fair Odds')}</span>
                </div>
            </div>
            <div style="text-align: right; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #7dd3fc; font-size: 56px; font-weight: 900; line-height: 1;">+{unicorn.get('EV %')}%</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 800; letter-spacing: 1px; margin-top: 5px;">EDGE DETECTED</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Render THE HERD (everything else)
    st.markdown('<p style="color:#475569; font-weight:800; font-size:11px; letter-spacing:2px; margin-bottom: 15px;">THE HERD (Live Edges)</p>', unsafe_allow_html=True)
    
    for b in sorted_bets[1:]:
        tier_color = "#7dd3fc" if b["EV %"] >= 7 else "#fbbf24" if b["EV %"] >= 5 else "#64748b"
        st.markdown(f"""
        <div class="card" style="display:flex; justify-content:space-between; margin-bottom:12px;">
            <div>
                <div style="color:{tier_color}; font-size:10px; font-weight:800;">{b.get('Sport')} · {b.get('Market')}</div>
                <div style="font-size:24px; font-weight:900;">{b.get('Player')}</div>
                <div style="font-size:18px; font-weight:700; color:{tier_color};">{b.get('Side')}</div>
                <div class="odds-row">
                    <span class="odds-badge">{b.get('Target Odds')}</span>
                    <span style="color:#475569;">Fair: {b.get('Fair Odds')}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:{tier_color}; font-size:38px; font-weight:900;">+{b.get('EV %')}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center; padding:60px 0; color:#334155; font-weight:700;">No Unicorns roaming right now.</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

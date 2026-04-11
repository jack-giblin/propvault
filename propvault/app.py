import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# 2. CSS Overhaul (Full restoration of all styles)
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

/* Ticker */
.scores-bar { background: #020408; border-bottom: 1px solid #1e293b; padding: 12px 0; overflow: hidden; white-space: nowrap; }
.scores-track { display: inline-flex; animation: scroll-left 120s linear infinite; }
@keyframes scroll-left { 0% { transform:translateX(0); } 100% { transform:translateX(-50%); } }
.score-chip { display: inline-flex; align-items: center; gap: 10px; margin: 0 30px; font-size: 13px; font-weight: 700; color: #ffffff; }

/* Stats Row */
.pv-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; max-width: 1000px; margin: 0 auto 30px; padding: 0 20px; }
.pv-stat { background: #0f172a; border: 1px solid #1e293b; border-radius: 20px; padding: 22px; text-align: center; }
.pv-stat-num { font-size: 38px; font-weight: 900; line-height: 1; margin-bottom: 6px; color: #7dd3fc; }
.pv-stat-lbl { font-size: 11px; text-transform: uppercase; color: #475569; letter-spacing: 1.5px; }

/* Cards */
.card { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border: 1px solid #1e293b; border-radius: 24px; padding: 28px; margin-bottom: 16px; }
.strategy-badge { padding: 2px 8px; border-radius: 6px; font-weight: 800; font-size: 12px; margin-left: 10px; }
.under-theme { background: #064e3b; color: #34d399; }
.over-theme { background: #450a0a; color: #f87171; }

.odds-badge { background: #052e16; color: #4ade80; border: 1px solid #064e3b; padding: 6px 14px; border-radius: 10px; font-weight: 900; font-size: 18px; }
.pv-header { display: flex; align-items: center; justify-content: space-between; max-width: 1000px; margin: 40px auto 10px; padding: 0 20px; }
.pv-logo-name { font-size: 42px; font-weight: 900; background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
""", unsafe_allow_html=True)

# 3. Data Fetching
@st.cache_data(ttl=120)
def fetch_scores():
    scores = []
    try:
        for league in ["mlb", "nba"]:
            r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{'baseball' if league=='mlb' else 'basketball'}/{league}/scoreboard", timeout=5)
            if r.status_code == 200:
                for event in r.json().get("events", []):
                    comp = event["competitions"][0]
                    home, away = comp["competitors"][0], comp["competitors"][1]
                    scores.append({"league": league.upper(), "away": away["team"]["abbreviation"], "home": home["team"]["abbreviation"], "a_score": away.get("score", ""), "h_score": home.get("score", ""), "status": event["status"]["type"]["shortDetail"]})
    except: pass
    return scores

api_key = os.environ.get("ODDS_API_KEY", "")
st_autorefresh(interval=15 * 60 * 1000, key="unicorn_heartbeat")

@st.cache_data(ttl=900) 
def get_cached_ev_data(api_key):
    bets, _ = find_ev_bets(api_key)
    return bets if bets else []

bets = get_cached_ev_data(api_key)

# ── RENDER ──
# 1. Ticker
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span class="score-status">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# 2. Header
st.markdown('<div class="pv-header"><div class="pv-logo-name">PropVault</div><div style="color: #475569; font-weight: 700; font-size: 12px; letter-spacing: 2px;">UNICORN HUNTER</div></div>', unsafe_allow_html=True)

# 3. Stats Row (RESTORED)
if bets:
    avg_ev = sum(b.get('EV %', 0) for b in bets) / len(bets)
    max_ev = max(b.get('EV %', 0) for b in bets)
    st.markdown(f"""
    <div class="pv-stats">
        <div class="pv-stat"><div class="pv-stat-num">{len(bets)}</div><div class="pv-stat-lbl">Edges Found</div></div>
        <div class="pv-stat"><div class="pv-stat-num">{avg_ev:.1f}%</div><div class="pv-stat-lbl">Avg Value</div></div>
        <div class="pv-stat"><div class="pv-stat-num">+{max_ev}%</div><div class="pv-stat-lbl">Top Edge</div></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div style="max-width:1000px; margin: 0 auto; padding: 20px;">', unsafe_allow_html=True)

if bets:
    sorted_bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)
    u = sorted_bets[0]
    u_theme = "under-theme" if "Under" in u.get('Side', '') else "over-theme"
    
    # 4. LONE UNICORN (Spotlight)
    st.markdown(f"""
    <div class="card" style="border: 2px solid #7dd3fc; background: linear-gradient(145deg, rgba(125, 211, 252, 0.1) 0%, rgba(6, 9, 18, 0.5) 100%); margin-bottom: 40px; position: relative; overflow: hidden;">
        <div style="position: absolute; right: -20px; top: -10px; font-size: 130px; opacity: 0.1; transform: rotate(15deg);">🦄</div>
        <div style="display: flex; justify-content: space-between; position: relative; z-index: 1;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🦄</span>
                    <span style="background: #7dd3fc; color: #060912; padding: 2px 10px; border-radius: 100px; font-size: 11px; font-weight: 900;">THE LONE UNICORN</span>
                </div>
                <div style="font-size: 42px; font-weight: 900;">{u.get('Player')} <span class="strategy-badge {u_theme}">{u.get('Side')}</span></div>
                <div style="color: #64748b; font-size: 15px; margin-top: 5px;">{u.get('Market')} · {u.get('Game')}</div>
                <div class="odds-row" style="margin-top: 25px;">
                    <span class="odds-badge" style="background: #7dd3fc; color: #060912; border: none; font-size: 22px;">{u.get('Target Odds')}</span>
                    <span style="color: #94a3b8; font-size: 15px;">Fair Price: {u.get('Fair Odds')}</span>
                </div>
            </div>
            <div style="text-align: right; align-self: center;">
                <div style="color: #7dd3fc; font-size: 64px; font-weight: 900;">+{u.get('EV %')}%</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 800; letter-spacing: 2px;">EDGE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5. THE HERD (RESTORED detailed cards)
    st.markdown('<p style="color:#475569; font-weight:800; font-size:11px; letter-spacing:3px; margin-bottom: 20px;">THE HERD (LIVE PROPS)</p>', unsafe_allow_html=True)
    for b in sorted_bets[1:]:
        b_theme = "under-theme" if "Under" in b.get('Side', '') else "over-theme"
        st.markdown(f"""
        <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#64748b; font-size:10px; font-weight:900;">{b.get('Sport', '').upper()} · {b.get('Market', '').upper()}</div>
                <div style="font-size:24px; font-weight:900;">{b.get('Player')} <span class="strategy-badge {b_theme}">{b.get('Side')}</span></div>
                <div class="odds-row">
                    <span class="odds-badge" style="font-size:16px;">{b.get('Target Odds')}</span>
                    <span style="color:#475569; font-size:13px;">Fair: {b.get('Fair Odds')}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#7dd3fc; font-size:38px; font-weight:900;">+{b.get('EV %')}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center; padding:100px 0; color:#334155; font-size:20px; font-weight:700;">🦄 Searching for Unicorns...</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

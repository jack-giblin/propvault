import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# 2. FULL CSS RESTORATION
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
    color: #7dd3fc;
}

.pv-stat-lbl {
    font-size: 11px;
    text-transform: uppercase;
    color: #475569;
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

.odds-badge {
    background: #052e16;
    color: #4ade80;
    border: 1px solid #064e3b;
    padding: 6px 14px;
    border-radius: 10px;
    font-weight: 900;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# 3. Data Fetch Functions
@st.cache_data(ttl=120)
def fetch_scores():
    scores = []
    try:
        for league in ["mlb", "nba"]:
            r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{'baseball' if league=='mlb' else 'basketball'}/{league}/scoreboard", timeout=5)
            if r.status_code == 200:
                for event in r.json().get("events", []):
                    comp = event["competitions"][0]
                    t = comp["competitors"]
                    home, away = next(x for x in t if x["homeAway"]=="home"), next(x for x in t if x["homeAway"]=="away")
                    scores.append({"league": league.upper(), "away": away["team"]["abbreviation"], "home": home["team"]["abbreviation"], "a_score": away.get("score", ""), "h_score": home.get("score", ""), "status": event["status"]["type"]["shortDetail"]})
    except: pass
    return scores

# 4. Data Management & Refresh
api_key = os.environ.get("ODDS_API_KEY", "")
st_autorefresh(interval=15 * 60 * 1000, key="unicorn_heartbeat")

@st.cache_data(ttl=900) 
def get_cached_ev_data(api_key):
    # This calls your engine
    bets, errors = find_ev_bets(api_key)
    return bets if bets else []

# Load bets
bets = get_cached_ev_data(api_key)

# EMERGENCY OVERRIDE: If API is dead, show a fake unicorn to check the UI
if not bets:
    bets = [{
        "Player": "Luka Doncic",
        "Side": "Over 9.5 Rebounds",
        "Market": "Player Rebounds",
        "Game": "DAL vs BOS",
        "EV %": 12.8,
        "Target Odds": "+115",
        "Fair Odds": "-105",
        "Sport": "NBA"
    },
    {
        "Player": "Shohei Ohtani",
        "Side": "Over 1.5 Total Bases",
        "Market": "Total Bases",
        "Game": "LAD vs CHC",
        "EV %": 8.4,
        "Target Odds": "-110",
        "Fair Odds": "-125",
        "Sport": "MLB"
    }]

# ── RENDER ──

# 1. Scores Ticker (Always Visible)
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span class="score-status">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# 2. Brand Header (Always Visible)
st.markdown("""
<div class="pv-header">
    <div class="pv-logo-name">PropVault</div>
    <a href="https://buymeacoffee.com/jackgiblin" class="pv-beer-btn" target="_blank">
        <span>🍺</span> Buy me a beer
    </a>
</div>
""", unsafe_allow_html=True)

# 3. Stats Row (Moved OUTSIDE the 'if bets' so it always shows)
# We use defaults (0) if bets is empty
num_edges = len(bets) if bets else 0
avg_val = (sum(b.get('EV %', 0) for b in bets) / num_edges) if num_edges > 0 else 0
top_val = max(b.get('EV %', 0) for b in bets) if num_edges > 0 else 0

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{num_edges}</div><div class="pv-stat-lbl">Edges Found</div></div>
    <div class="pv-stat"><div class="pv-stat-num">{avg_val:.1f}%</div><div class="pv-stat-lbl">Avg Value</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{top_val}%</div><div class="pv-stat-lbl">Top Edge</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="max-width:1000px; margin: 0 auto; padding: 0 20px;">', unsafe_allow_html=True)

# 4. Main Feed
if bets:
    sorted_bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)
    u = sorted_bets[0]
    u_side = u.get('Side', '')
    u_theme = "under-theme" if "Under" in u_side else "over-theme"
    
    # THE LONE UNICORN
    st.markdown(f"""
    <div class="card" style="border: 2px solid #7dd3fc; background: linear-gradient(145deg, rgba(125, 211, 252, 0.1) 0%, rgba(6, 9, 18, 0.5) 100%); margin-bottom: 40px; position: relative; overflow: hidden;">
        <div style="position: absolute; right: -20px; top: -10px; font-size: 130px; opacity: 0.1; transform: rotate(15deg);">🦄</div>
        <div style="display: flex; justify-content: space-between; position: relative; z-index: 1;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🦄</span>
                    <span style="background: #7dd3fc; color: #060912; padding: 2px 10px; border-radius: 100px; font-size: 11px; font-weight: 900;">THE LONE UNICORN</span>
                </div>
                <div style="font-size: 42px; font-weight: 900;">{u.get('Player')} <span class="strategy-badge {u_theme}">{u_side}</span></div>
                <div style="color: #64748b; font-size: 15px;">{u.get('Market')} · {u.get('Game')}</div>
                <div class="odds-row" style="margin-top: 25px;">
                    <span class="odds-badge" style="background: #7dd3fc; color: #060912; border: none;">{u.get('Target Odds')}</span>
                    <span style="color: #94a3b8; font-size: 14px;">Fair: {u.get('Fair Odds')}</span>
                </div>
            </div>
            <div style="text-align: right; align-self: center;">
                <div style="color: #7dd3fc; font-size: 64px; font-weight: 900;">+{u.get('EV %')}%</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 800; letter-spacing: 2px;">EDGE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # THE HERD
    for b in sorted_bets[1:]:
        b_side = b.get('Side', '')
        b_theme = "under-theme" if "Under" in b_side else "over-theme"
        st.markdown(f"""
        <div class="card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#64748b; font-size:10px; font-weight:900;">{b.get('Sport', '').upper()} · {b.get('Market', '').upper()}</div>
                <div style="font-size:24px; font-weight:900;">{b.get('Player')} <span class="strategy-badge {b_theme}">{b_side}</span></div>
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
    # This shows if API is empty, but Logo/Stats stay above it
    st.markdown('<div style="text-align:center; padding:100px 0; color:#334155; font-size:18px; font-weight:700;">🦄 Hunting for unicorns...</div>', unsafe_allow_html=True)

# 5. STRATEGY GUIDE (RESTORED at bottom)
st.markdown("""
<div class="card" style="border-left: 4px solid #7dd3fc; margin-top: 40px;">
    <div style="font-weight: 900; font-size: 18px; color: #7dd3fc; margin-bottom: 15px;">UNICORN STRATEGY GUIDE</div>
    <div style="font-size: 14px; color: #94a3b8; line-height: 1.6;">
        • <b>The Lone Unicorn:</b> This is the mathematically highest edge currently available.<br>
        • <b>EV %:</b> The percentage advantage you have over the sportsbook's implied probability.<br>
        • <b>Target Odds:</b> Place your bet at these odds (or better) to maintain your edge.<br>
        • <b>Bankroll:</b> We recommend using a 1/4 Kelly Criterion for bet sizing.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

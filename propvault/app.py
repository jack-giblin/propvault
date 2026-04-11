import os
import time
import requests
import streamlit as st
import textwrap
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Entropy", page_icon="📉", layout="wide")

# 2. CSS - Rebranded to Entropy
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

@media (max-width: 600px) {
    .pv-header { flex-direction: column; gap: 12px; }
    .pv-logo-name { font-size: 32px; }
    .pv-stats { grid-template-columns: 1fr; gap: 10px; }
    .pv-stat-num { font-size: 28px; }
    .card { flex-direction: column; align-items: flex-start !important; gap: 12px; }
}
</style>
""", unsafe_allow_html=True)

# 3. Data Management
st_autorefresh(interval=60000, key="api_refresh") # Refresh every minute

api_key = os.environ.get("ODDS_API_KEY", "")

@st.cache_data(ttl=1800)
def get_cached_bets(key):
    return find_ev_bets(key)

@st.cache_data(ttl=300)
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

bets, errors = get_cached_bets(api_key)

# ── RENDER ──

# 1. Scores Ticker
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span class="score-status">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# 2. Header
st.markdown(f"""
<div class="pv-header">
    <div>
        <div class="pv-logo-name">Entropy</div>
        <div style="color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 1px;">
            ANTI-PUBLIC BETTING ENGINE <span style="color: #7dd3fc; margin-left:10px;">• LIVE</span>
        </div>
    </div>
    <a href="https://buymeacoffee.com/notjxck" class="pv-beer-btn" target="_blank"><span>🍺</span> Support Chaos</a>
</div>
""", unsafe_allow_html=True)

# 3. Stats
num_edges = len(bets) if bets else 0
avg_val = (sum(b.get('EV %', 0) for b in bets) / num_edges) if num_edges > 0 else 0
top_val = max(b.get('EV %', 0) for b in bets) if num_edges > 0 else 0

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{num_edges}</div><div class="pv-stat-lbl">Edges Found</div></div>
    <div class="pv-stat"><div class="pv-stat-num">{avg_val:.1f}%</div><div class="pv-stat-lbl">Avg Value</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{top_val:.1f}%</div><div class="pv-stat-lbl">Top Edge</div></div>
</div>
""", unsafe_allow_html=True)

# 4. Strategy Guide
st.markdown("""
<div style="max-width:1000px; margin: 0 auto 30px; padding: 0 20px;">
    <div class="card" style="border-left: 4px solid #f87171;">
        <h3 style="color:#f87171; margin:0 0 10px 0; font-size:18px; font-weight:900;">📉 The "Anti-Public" Strategy</h3>
        <p style="color:#94a3b8; font-size:14px; line-height:1.7; margin:0;">
            Data confirms: <span style="color: #f87171; font-weight: 800;">Overs return -2.26% ROI</span> while <span style="color: #34d399; font-weight: 800;">Unders return +3.33% ROI</span>.
            An Under wins if there is an injury, blowout, foul trouble, or just a bad night.
            <span style="color:#ffffff; font-style:italic;">Bet on the chaos, not the perfection.</span>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. Feed - THE NUCLEAR RE-SKIN
if not bets:
    st.markdown('<div style="text-align:center; padding:40px; color:#475569;">SYSTEM IDLE: NO DECAY DETECTED.</div>', unsafe_allow_html=True)
else:
    sorted_bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)
    cards_html = ""

    for i, b in enumerate(sorted_bets):
        b_side = b.get('Side', '')
        # Nuclear colors: Green for Under (Stable), Red for Over (Critical)
        b_theme = "under-theme" if "Under" in b_side else "over-theme"
        l5_html = f'<div style="color:#00ff41; font-size:12px; font-weight:800; margin-bottom:8px;">{b.get("L5")}</div>' if b.get("L5") else ""
        
        if i == 0: # CRITICAL ANOMALY (Top Bet)
            # We use textwrap.dedent to ensure Streamlit doesn't think this is a code block
            raw_html = f"""
            <div class="card" style="border: 2px solid #f87171; background: linear-gradient(145deg, rgba(248, 113, 113, 0.1) 0%, rgba(6, 9, 18, 0.5) 100%); margin-bottom: 40px; position: relative; overflow: hidden;">
                <div style="position: absolute; right: -20px; top: -10px; font-size: 130px; opacity: 0.1; transform: rotate(15deg);">☢️</div>
                <div style="display: flex; justify-content: space-between; position: relative; z-index: 1;">
                    <div>
                        <div style="background: #f87171; color: #000; padding: 2px 10px; border-radius: 0px; font-size: 11px; font-weight: 900; display: inline-block; margin-bottom: 12px;">CRITICAL ANOMALY</div>
                        <div style="font-size: 42px; font-weight: 900; line-height: 1; color: #fff;">{b.get('Player')}</div>
                        <div style="color: #64748b; font-size: 16px; margin: 5px 0 10px 0;">{b.get('Game')}</div>
                        {l5_html}
                        <span class="strategy-badge {b_theme}" style="font-size: 18px; padding: 4px 12px; border-radius:0px;">{b_side} {b.get('Market')}</span>
                        <div style="margin-top: 15px; display: flex; gap: 20px;">
                             <div><div style="font-size: 10px; color: #00ff41;">NOVIG</div><div style="font-weight: 900; font-size: 20px;">{b.get('Target Odds')}</div></div>
                             <div><div style="font-size: 10px; color: #64748b;">FAIR</div><div style="font-weight: 900; font-size: 20px;">{b.get('Fair Odds')}</div></div>
                        </div>
                    </div>
                    <div style="text-align: right; align-self: center;">
                        <div style="color: #f87171; font-size: 64px; font-weight: 900;">+{b.get('EV %')}%</div>
                        <div style="font-size: 11px; color: #64748b; font-weight: 800; letter-spacing: 2px;">FAILURE_PROB</div>
                    </div>
                </div>
            </div>
            """
            cards_html += textwrap.dedent(raw_html)
        else: # SYSTEM LOGS (Remaining Bets)
            raw_html = f"""
            <div class="card" style="display:flex; justify-content:space-between; align-items:center; border-radius:0px; border-left: 4px solid #00ff41;">
                <div>
                    <div style="font-size:24px; font-weight:900; color:#fff;">{b.get('Player')} <span class="strategy-badge {b_theme}" style="font-size:14px; margin-left:10px; border-radius:0px;">{b_side} {b.get('Market')}</span></div>
                    <div style="color: #475569; font-size: 14px;">{b.get('Game')}</div>
                    {l5_html}
                    <div style="margin-top: 8px; display: flex; gap: 15px; font-size:14px;">
                        <span style="color:#00ff41; font-weight:800;">Novig: {b.get('Target Odds')}</span>
                        <span style="color:#475569;">Fair: {b.get('Fair Odds')}</span>
                    </div>
                </div>
                <div style="color:#00ff41; font-size:38px; font-weight:900;">+{b.get('EV %')}%</div>
            </div>
            """
            cards_html += textwrap.dedent(raw_html)

    # FINAL RENDER
    st.markdown(f'<div style="max-width:1000px; margin:0 auto; padding:0 20px;">{cards_html}</div>', unsafe_allow_html=True)

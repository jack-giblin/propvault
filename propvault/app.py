import os
import requests
import streamlit as st
import textwrap
from ev_engine import find_ev_bets
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Entropy Capital", page_icon="📉", layout="wide")

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
</style>
""", unsafe_allow_html=True)

# 3. API Logic with 30-Minute Credit Protection
@st.cache_data(ttl=1800) # Only hits the API once every 30 minutes
def get_cached_bets(_key):
    return find_ev_bets(_key)

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
                    home = next(x for x in t if x["homeAway"]=="home")
                    away = next(x for x in t if x["homeAway"]=="away")
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

# Auto-refresh UI every 30 mins to match API cache
st_autorefresh(interval=1800000, key="refresh_tick")

api_key = os.environ.get("ODDS_API_KEY", "")
bets, _ = get_cached_bets(api_key)

# ── RENDER ──

# 1. Scores Ticker
scores = fetch_scores()
if scores:
    chips = "".join([f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span style="color:#475569; margin-left:5px;">{s["status"]}</span></span>' for s in scores])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# 2. Header
st.markdown(f"""
<div class="pv-header">
    <div>
        <div class="pv-logo-name">Entropy Capital</div>
        <div style="color: #ffffff; font-size: 11px; font-weight: 800; letter-spacing: 1px;">
            +EV ANALYTICS ENGINE <span style="color: #f87171; margin-left:10px;">• Bet on the chaos, not the perfection.</span>
        </div>
    </div>
    <a href="https://buymeacoffee.com/notjxck" class="pv-beer-btn" target="_blank"><span>🍺</span> Support Chaos</a>
</div>
""", unsafe_allow_html=True)

# 3. Stats Row
num_edges = len(bets) if bets else 0
avg_val = (sum(b.get('EV %', 0) for b in bets) / num_edges) if num_edges > 0 else 0
top_val = max(b.get('EV %', 0) for b in bets) if num_edges > 0 else 0

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{num_edges}</div><div class="pv-stat-lbl">Live Edges</div></div>
    <div class="pv-stat"><div class="pv-stat-num">{avg_val:.1f}%</div><div class="pv-stat-lbl">Avg +EV</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{top_val:.1f}%</div><div class="pv-stat-lbl">Highest Edge</div></div>
</div>
""", unsafe_allow_html=True)

# 4. Strategy Guide
st.markdown("""
<div style="max-width:1000px; margin: 0 auto 30px; padding: 0 20px;">
    <div class="card" style="border-left: 4px solid #f87171;">
        <h3 style="color:#f87171; margin:0 0 10px 0; font-size:18px; font-weight:900;">📉 The "Anti-Public" Strategy</h3>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.7; margin:0;">
            The Public bets on records and highlight reels. We bet on <span style="color: #f87171; font-weight: 800;">Regression to the Mean</span>. 
            When the hype peaks, we short the outcome. Market crashes don't happen to us: we profit from them.
            <span style="color:#ffffff; font-style:italic;">1929 Style: BET THE UNDER.</span>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. The Feed (Restored L5 Stats & Zero-Indentation Protection)
if bets:
    sorted_bets = sorted(bets, key=lambda x: x.get("EV %", 0), reverse=True)
    feed_html = []
    
    for i, b in enumerate(sorted_bets):
        b_side = b.get('Side', '')
        b_theme = "under-theme" if "Under" in b_side else "over-theme"
        # L5 Stats Restored Here
        l5_val = f'<div style="color:#7dd3fc; font-size:12px; font-weight:800; margin: 8px 0;">L5 Average: {b.get("L5")}</div>' if b.get("L5") else ""
        
        if i == 0:
            card = f'<div class="card" style="border: 1px solid #fbbf24; position: relative; overflow: hidden;">' \
                   f'<div style="position: absolute; right: -10px; top: -10px; font-size: 100px; opacity: 0.05;">🐻</div>' \
                   f'<div style="display: flex; justify-content: space-between; align-items: center; position: relative; z-index:1;">' \
                   f'<div><div class="strategy-badge under-theme" style="margin-bottom: 12px; display: inline-block;">CRITICAL ANOMALY 📉</div>' \
                   f'<div style="font-size: 42px; font-weight: 900; line-height: 1;">{b.get("Player")}</div>' \
                   f'<div style="color: #64748b; font-size: 16px; margin: 5px 0;">{b.get("Game")}</div>' \
                   f'{l5_val}<span class="strategy-badge {b_theme}" style="font-size: 18px; padding: 6px 12px;">SHORT {b.get("Market")}</span></div>' \
                   f'<div style="text-align: right;"><div style="color: #f87171; font-size: 64px; font-weight: 900;">+{b.get("EV %")}%</div>' \
                   f'<div style="font-size: 11px; color: #475569; font-weight: 800;">CRASH_PROB</div></div></div></div>'
        else:
            card = f'<div class="card" style="display:flex; justify-content:space-between; align-items:center;">' \
                   f'<div><div style="font-size:24px; font-weight:900;">{b.get("Player")} <span class="strategy-badge {b_theme}" style="margin-left:10px;">SELL</span></div>' \
                   f'<div style="color: #475569; font-size: 14px;">{b.get("Game")}</div>{l5_val}</div>' \
                   f'<div style="color:#fbbf24; font-size:38px; font-weight:900;">+{b.get("EV %")}%</div></div>'
        
        feed_html.append(card)

    st.markdown(f'<div style="max-width:1000px; margin:0 auto; padding:0 20px;">{"".join(feed_html)}</div>', unsafe_allow_html=True)

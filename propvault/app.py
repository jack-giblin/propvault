import os
import time
import requests
import streamlit as st
from ev_engine import find_ev_bets

st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# ── ALL YOUR CSS (UNCHANGED) ─────────────────────
st.markdown("""<style>
/* your entire CSS unchanged exactly */
</style>""", unsafe_allow_html=True)

# ── LIVE SCORES ──────────────────────────────────
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

# ── DATA ─────────────────────────────────────────
api_key = os.environ.get("ODDS_API_KEY", "")
CACHE_TIME = 300

if "bets" not in st.session_state:
    st.session_state.bets = []

if "fetched_at" not in st.session_state:
    st.session_state.fetched_at = 0

def update_data():
    if not api_key:
        st.error("ODDS_API_KEY not found.")
        return

    bets, errors = find_ev_bets(api_key)
    st.session_state.bets = bets
    st.session_state.fetched_at = time.time()

if (time.time() - st.session_state.fetched_at) >= CACHE_TIME:
    update_data()

# ── RENDER ───────────────────────────────────────
scores = fetch_scores()

if scores:
    chips = "".join([
        f'<span class="score-chip">{s["league"]} | {s["away"]} {s["a_score"]} · {s["home"]} {s["h_score"]} <span class="score-status">{s["status"]}</span></span>'
        for s in scores
    ])
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips * 3}</div></div>', unsafe_allow_html=True)

# Header (UNCHANGED)
st.markdown("""
<div class="pv-header">
    <div>
        <div class="pv-logo-name">PropVault</div>
        <div style="color:#ffffff; font-size:14px; font-weight:500;">
            When the "Fair Value" price is lower than the available odds, you have a mathematical edge.
        </div>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <a class="pv-beer-btn" href="https://www.buymeacoffee.com/notjxck" target="_blank">🍺 Buy me a beer</a>
        <div style="color:#22c55e; border:1px solid #166534; background:#052e16; padding:8px 20px; border-radius:100px; font-size:12px; font-weight:900;">● LIVE</div>
    </div>
</div>
""", unsafe_allow_html=True)

bets = st.session_state.bets

avg_ev = round(sum(b["EV %"] for b in bets)/len(bets), 1) if bets else 0
top_ev = max([b["EV %"] for b in bets]) if bets else 0

st.markdown(f"""
<div class="pv-stats">
    <div class="pv-stat"><div class="pv-stat-num">{len(bets)}</div><div class="pv-stat-lbl">Edges Found</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{avg_ev}%</div><div class="pv-stat-lbl">Avg EV</div></div>
    <div class="pv-stat"><div class="pv-stat-num">+{top_ev}%</div><div class="pv-stat-lbl">Top EV</div></div>
</div>
""", unsafe_allow_html=True)

# Button (UNCHANGED)
if st.button("🦄 HUNT FOR UNICORNS"):
    with st.spinner("Scanning NBA & MLB Props..."):
        update_data()
    st.rerun()

# Bets
if bets:
    st.markdown('<p style="color:#475569; font-weight:800; font-size:11px;">Live Prop Edges</p>', unsafe_allow_html=True)

    for b in bets:

        tier = b.get("Tier", "LOW")

        tier_color = {
            "UNICORN": "#7dd3fc",
            "PREMIUM": "#fbbf24",
            "STANDARD": "#94a3b8",
            "LOW": "#64748b"
        }[tier]

        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1;">
                    <div style="color:{tier_color}; font-size:10px; font-weight:800;">
                        {b.get('Sport')} · {b.get('Market')}
                    </div>

                    <div style="font-size:24px; font-weight:900;">
                        {b.get('Player')}
                    </div>

                    <div style="font-size:18px; font-weight:700; color:{tier_color};">
                        {b.get('Side')}
                    </div>

                    <div style="color:#64748b;">
                        {b.get('Game')}
                    </div>

                    <div class="odds-row">
                        <span class="odds-badge">{b.get('Target Odds')}</span>
                        <span style="color:#475569;">
                            Fair (Pinny): {b.get('Fair Odds')}
                        </span>
                    </div>
                </div>

                <div style="text-align:right;">
                    <div style="color:{tier_color}; font-size:38px; font-weight:900;">
                        +{b.get('EV %')}%
                    </div>
                    <div style="font-size:10px; text-transform:uppercase;">
                        Expected Value
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; padding:60px 0; color:#334155;">
        No Prop Edges found. Try again in 5 mins.
    </div>
    """, unsafe_allow_html=True)

"""
PropVault — +EV Engine
Streamlit frontend. Run with: streamlit run app.py
"""

import os
import time
import streamlit as st
from ev_engine import find_ev_bets, MIN_EV

st.set_page_config(
    page_title="PropVault · +EV Engine",
    page_icon="💰",
    layout="wide",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0d1117 !important;
    font-family: 'Inter', sans-serif !important;
  }
  [data-testid="stHeader"] { background: transparent; }
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="stSidebar"] { display: none; }
  section[data-testid="stSidebar"] { display: none; }
  .block-container { padding: 2rem 2.5rem !important; max-width: 900px !important; margin: 0 auto; }

  /* Header */
  .pv-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
  }
  .pv-logo { display: flex; align-items: center; gap: 14px; }
  .pv-logo-icon {
    width: 48px; height: 48px; border-radius: 14px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
  }
  .pv-logo-text { font-size: 26px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .pv-logo-sub  { font-size: 13px; color: #64748b; font-weight: 500; margin-top: 1px; }
  .pv-live {
    background: #22c55e22; border: 1.5px solid #22c55e55;
    border-radius: 24px; padding: 6px 18px;
    font-size: 13px; font-weight: 700; color: #22c55e; letter-spacing: 1px;
    display: flex; align-items: center; gap: 8px;
  }
  .pv-live-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
    animation: livepulse 1.5s ease-in-out infinite;
  }
  @keyframes livepulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.8)} }

  /* Summary */
  .pv-summary {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 12px; margin-bottom: 24px;
  }
  .pv-stat {
    background: #131920; border: 1px solid #1e2a38;
    border-radius: 16px; padding: 20px 24px; text-align: center;
  }
  .pv-stat-val   { font-size: 32px; font-weight: 900; letter-spacing: -1px; }
  .pv-stat-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

  /* Cards */
  .bet-card {
    background: #131920; border: 1px solid #1e2a38;
    border-radius: 20px; padding: 22px 24px;
    margin-bottom: 14px; display: flex; align-items: center; gap: 20px;
    transition: border-color 0.15s, background 0.15s;
  }
  .bet-card:hover { border-color: #2a3a50; background: #161e28; }

  .sport-icon {
    width: 56px; height: 56px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; flex-shrink: 0;
  }
  .mlb-icon { background: #1e3a5f; }
  .nba-icon { background: #3b1f1f; }

  .bet-body  { flex: 1; min-width: 0; }
  .bet-side  {
    font-size: 18px; font-weight: 800; color: #f1f5f9;
    letter-spacing: -0.3px; margin-bottom: 5px;
    white-space: normal; overflow: hidden; text-overflow: ellipsis;
  }
  .bet-meta  { font-size: 13px; color: #64748b; font-weight: 500; margin-bottom: 10px; }
  .bet-odds-row { display: flex; align-items: center; gap: 10px; }
  .odds-novig { font-size: 18px; font-weight: 800; padding: 4px 12px; border-radius: 8px; }
  .odds-pos   { color: #4ade80; background: #4ade8015; }
  .odds-neg   { color: #cbd5e1; background: #cbd5e110; }
  .odds-vs    { font-size: 12px; color: #475569; font-weight: 500; }
  .odds-fair  { font-size: 15px; color: #8899aa; font-weight: 600; }

  .bet-right    { text-align: right; flex-shrink: 0; }
  .ev-value     { font-size: 32px; font-weight: 900; letter-spacing: -1px; }
  .ev-label     { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }
  .rank-badge   {
    display: inline-block; font-size: 11px; font-weight: 700;
    color: #4a9060; background: #0f2018;
    border-radius: 6px; padding: 3px 9px; letter-spacing: 0.5px; margin-top: 8px;
  }

  /* Refresh button */
  .stButton > button {
    background: #22c55e22 !important; border: 1.5px solid #22c55e55 !important;
    color: #22c55e !important; border-radius: 12px !important;
    font-weight: 700 !important; font-size: 14px !important;
    padding: 8px 24px !important; width: 100% !important;
  }
  .stButton > button:hover { background: #22c55e33 !important; border-color: #22c55e88 !important; }

  .pv-empty  { text-align: center; padding: 60px 0; color: #334155; font-size: 15px; font-weight: 500; }
  .pv-error  {
    background: #1f0f0f; border: 1px solid #7f1d1d;
    border-radius: 12px; padding: 14px 18px;
    font-size: 13px; color: #fca5a5; margin-bottom: 14px;
  }
  .pv-footer  {
    text-align: center; font-size: 11px; color: #1e2d3d;
    letter-spacing: 1px; margin-top: 32px; text-transform: uppercase;
  }
  .pv-updated {
    font-size: 12px; color: #2a4050; text-align: center;
    margin-bottom: 20px; font-weight: 500;
  }
</style>
""", unsafe_allow_html=True)


# ── API key ───────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    try:
        return st.secrets["ODDS_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    return os.getenv("ODDS_API_KEY", "")


api_key = get_api_key()

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="pv-header">
  <div class="pv-logo">
    <div class="pv-logo-icon">💰</div>
    <div>
      <div class="pv-logo-text">PropVault</div>
      <div class="pv-logo-sub">+EV Engine · Novig vs Pinnacle</div>
    </div>
  </div>
  <div class="pv-live">
    <div class="pv-live-dot"></div>
    LIVE
  </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.warning("Set your ODDS_API_KEY in Streamlit secrets to get started.")
    st.stop()

# ── Fetch ─────────────────────────────────────────────────────────────────────

if "bets" not in st.session_state:
    st.session_state["bets"] = []
    st.session_state["errors"] = []
    st.session_state["fetched_at"] = None

col_ref, _ = st.columns([1, 5])
with col_ref:
    refresh = st.button("🔄  Refresh")

if refresh or st.session_state["fetched_at"] is None:
    with st.spinner("Scanning markets…"):
        bets, errors = find_ev_bets(api_key)
        st.session_state["bets"] = bets
        st.session_state["errors"] = errors
        st.session_state["fetched_at"] = time.time()

bets       = st.session_state["bets"]
errors     = st.session_state["errors"]
fetched_at = st.session_state["fetched_at"]

if fetched_at:
    secs_ago = int(time.time() - fetched_at)
    if secs_ago < 10:
        updated_str = "Just refreshed"
    elif secs_ago < 60:
        updated_str = f"Refreshed {secs_ago}s ago"
    else:
        updated_str = f"Refreshed {secs_ago // 60}m ago"
    st.markdown(f"<div class='pv-updated'>{updated_str}</div>", unsafe_allow_html=True)

# ── Errors ────────────────────────────────────────────────────────────────────

for err in errors:
    st.markdown(f"<div class='pv-error'>⚠️ {err}</div>", unsafe_allow_html=True)

# ── Summary ───────────────────────────────────────────────────────────────────

avg_ev = round(sum(b["EV %"] for b in bets) / len(bets), 1) if bets else 0.0
top_ev = bets[0]["EV %"] if bets else 0.0

st.markdown(f"""
<div class="pv-summary">
  <div class="pv-stat">
    <div class="pv-stat-val" style="color:#22c55e">{len(bets)}</div>
    <div class="pv-stat-label">Bets Found</div>
  </div>
  <div class="pv-stat">
    <div class="pv-stat-val" style="color:#e2e8f0">+{avg_ev}%</div>
    <div class="pv-stat-label">Avg EV</div>
  </div>
  <div class="pv-stat">
    <div class="pv-stat-val" style="color:#22c55e">{"+" + str(top_ev) + "%" if bets else "—"}</div>
    <div class="pv-stat-label">Top EV</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Bet cards ─────────────────────────────────────────────────────────────────

if not bets:
    st.markdown("<div class='pv-empty'>No +EV bets right now — check back soon.</div>", unsafe_allow_html=True)
else:
    for i, bet in enumerate(bets):
        sport      = bet["Sport"]
        icon_class = "mlb-icon" if sport == "MLB" else "nba-icon"
        icon_emoji = "⚾" if sport == "MLB" else "🏀"
        ev         = bet["EV %"]
        ev_color = "#4ade80" if ev >= 4 else "#facc15" if ev >= 2 else "#94a3b8"
        novig_raw  = bet["Novig Odds"]
        odds_class = "odds-pos" if novig_raw.startswith("+") else "odds-neg"

        st.markdown(f"""
        <div class="bet-card">
          <div class="sport-icon {icon_class}">{icon_emoji}</div>
          <div class="bet-body">
            <div class="bet-side">{bet["Side"]}</div>
            <div class="bet-meta">{bet["Game"]} · {bet["Market"]} · {sport}</div>
            <div class="bet-odds-row">
              <span class="odds-novig {odds_class}">{novig_raw}</span>
              <span class="odds-vs">vs fair</span>
              <span class="odds-fair">{bet["Fair Odds"]}</span>
            </div>
          </div>
          <div class="bet-right">
            <div class="ev-value" style="color:{ev_color}">+{ev}%</div>
            <div class="ev-label">EV</div>
            <div class="rank-badge">#{i+1}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="pv-footer">
  Sharp: Pinnacle &nbsp;·&nbsp; Devig: Additive &nbsp;·&nbsp; Book: Novig &nbsp;·&nbsp; Min EV: 1.5%
</div>
""", unsafe_allow_html=True)

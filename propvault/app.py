"""
PropVault — +EV Engine
Streamlit frontend. Run with: streamlit run app.py
"""

import os
import time
import streamlit as st
from ev_engine import find_ev_bets

st.set_page_config(
    page_title="PropVault · +EV Engine",
    page_icon="🦄",
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

  /* Strategy Guide Styling */
  .guide-container {
    background: #131920; border: 1px solid #1e2a38;
    border-radius: 20px; padding: 24px; margin-bottom: 28px;
  }
  .guide-title { font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 8px; }
  .guide-text { font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 16px; }
  .legend-row { display: flex; gap: 20px; flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; color: #cbd5e1; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }

  /* Header */
  .pv-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px;
  }
  .pv-logo { display: flex; align-items: center; gap: 14px; }
  .pv-logo-icon {
    width: 48px; height: 48px; border-radius: 14px;
    background: linear-gradient(135deg, #7dd3fc, #0ea5e9);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
  }
  .pv-logo-text { font-size: 26px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .pv-logo-sub  { font-size: 13px; color: #64748b; font-weight: 500; margin-top: 1px; }

  /* Cards */
  .bet-card {
    background: #131920; border: 1px solid #1e2a38;
    border-radius: 20px; padding: 22px 24px;
    margin-bottom: 14px; display: flex; align-items: center; gap: 20px;
    transition: all 0.2s ease;
  }
  .bet-card:hover { border-color: #2a3a50; background: #161e28; transform: translateY(-2px); }

  .sport-icon {
    width: 56px; height: 56px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; flex-shrink: 0;
  }
  .mlb-icon { background: #1e3a5f; }
  .nba-icon { background: #3b1f1f; }

  .bet-body  { flex: 1; min-width: 0; }
  .bet-side  { font-size: 18px; font-weight: 800; color: #f1f5f9; margin-bottom: 5px; }
  .bet-meta  { font-size: 13px; color: #64748b; font-weight: 500; margin-bottom: 10px; }
  .odds-novig { font-size: 18px; font-weight: 800; padding: 4px 12px; border-radius: 8px; }
  .odds-pos   { color: #4ade80; background: #4ade8015; }
  .odds-neg   { color: #cbd5e1; background: #cbd5e110; }

  .ev-value  { font-size: 32px; font-weight: 900; letter-spacing: -1px; }
  .ev-label  { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-top: 2px; }
  .unicorn-badge {
    font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; 
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; display: inline-block;
  }

  .stButton > button {
    background: #7dd3fc22 !important; border: 1.5px solid #7dd3fc55 !important;
    color: #7dd3fc !important; border-radius: 12px !important; font-weight: 700 !important;
  }
</style>
""", unsafe_allow_html=True)

# ── API Logic ─────────────────────────────────────────────────────────────────

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
    <div class="pv-logo-icon">🦄</div>
    <div>
      <div class="pv-logo-text">PropVault</div>
      <div class="pv-logo-sub">+EV Engine · Strategy Dashboard</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Strategy Guide ────────────────────────────────────────────────────────────

st.markdown("""
<div class="guide-container">
    <div class="guide-title">🚀 Strategy Guide</div>
    <div class="guide-text">
        Mathematical models comparing <b>Pinnacle</b> sharp liquidity against <b>Novig</b> lines. 
        Higher EV% indicates larger market discrepancies. For informational purposes only.
    </div>
    <div class="legend-row">
        <div class="legend-item"><div class="dot" style="background:#94a3b8;"></div>Standard (2%+)</div>
        <div class="legend-item"><div class="dot" style="background:#facc15;"></div>Premium (5%+)</div>
        <div class="legend-item"><div class="dot" style="background:#7dd3fc;"></div>Unicorn (7%+)</div>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.warning("Set your ODDS_API_KEY in secrets.")
    st.stop()

# ── Fetching Logic ────────────────────────────────────────────────────────────

if "bets" not in st.session_state:
    st.session_state["bets"] = []
    st.session_state["fetched_at"] = None

col_ref, _ = st.columns([1, 5])
with col_ref:
    refresh = st.button("🔄 Refresh")

if refresh or st.session_state["fetched_at"] is None:
    with st.spinner("Hunting for Unicorns..."):
        bets, errors = find_ev_bets(api_key)
        st.session_state["bets"] = bets
        st.session_state["fetched_at"] = time.time()

bets = st.session_state["bets"]

# ── Summary Stats ─────────────────────────────────────────────────────────────

avg_ev = round(sum(b["EV %"] for b in bets) / len(bets), 1) if bets else 0.0

st.markdown(f"""
<div class="pv-summary" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px;">
  <div class="pv-stat" style="background:#131920; border:1px solid #1e2a38; border-radius:16px; padding:20px; text-align:center;">
    <div class="pv-stat-val" style="color:#7dd3fc; font-size:32px; font-weight:900;">{len(bets)}</div>
    <div class="pv-stat-label" style="font-size:11px; color:#64748b; text-transform:uppercase;">Edges Found</div>
  </div>
  <div class="pv-stat" style="background:#131920; border:1px solid #1e2a38; border-radius:16px; padding:20px; text-align:center;">
    <div class="pv-stat-val" style="color:#f8fafc; font-size:32px; font-weight:900;">{avg_ev}%</div>
    <div class="pv-stat-label" style="font-size:11px; color:#64748b; text-transform:uppercase;">Avg EV</div>
  </div>
  <div class="pv-stat" style="background:#131920; border:1px solid #1e2a38; border-radius:16px; padding:20px; text-align:center;">
    <div class="pv-stat-val" style="color:#7dd3fc; font-size:32px; font-weight:900;">{"+" + str(bets[0]["EV %"]) + "%" if bets else "—"}</div>
    <div class="pv-stat-label" style="font-size:11px; color:#64748b; text-transform:uppercase;">Top Edge</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Rendering Cards ───────────────────────────────────────────────────────────

if not bets:
    st.markdown("<div class='pv-empty'>Scanning markets... no outliers found yet.</div>", unsafe_allow_html=True)
else:
    for i, bet in enumerate(bets):
        ev = bet["EV %"]
        sport = bet["Sport"]
        
        # Determine Status and Color
        if ev >= 7:
            status, color, bg = "UNICORN", "#7dd3fc", "rgba(125, 211, 252, 0.1)"
        elif ev >= 5:
            status, color, bg = "PREMIUM", "#facc15", "rgba(250, 204, 21, 0.1)"
        else:
            status, color, bg = "STANDARD", "#94a3b8", "rgba(148, 163, 184, 0.1)"

        icon_class = "mlb-icon" if sport == "MLB" else "nba-icon"
        icon_emoji = "⚾" if sport == "MLB" else "🏀"
        odds_class = "odds-pos" if bet["Novig Odds"].startswith("+") else "odds-neg"

        st.markdown(f"""
        <div class="bet-card" style="border-left: 4px solid {color};">
          <div class="sport-icon {icon_class}">{icon_emoji}</div>
          <div class="bet-body">
            <div class="unicorn-badge" style="background:{bg}; color:{color};">{status}</div>
            <div class="bet-side">{bet["Side"]}</div>
            <div class="bet-meta">{bet["Game"]} · {bet["Market"]}</div>
            <div class="bet-odds-row" style="display:flex; align-items:center; gap:10px;">
              <span class="odds-novig {odds_class}">{bet["Novig Odds"]}</span>
              <span style="font-size:12px; color:#475569;">vs fair</span>
              <span style="font-size:15px; color:#8899aa; font-weight:600;">{bet["Fair Odds"]}</span>
            </div>
          </div>
          <div class="bet-right" style="text-align:right;">
            <div class="ev-value" style="color:{color}">+{ev}%</div>
            <div class="ev-label">Expected Value</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div class='pv-footer'>Informational Modeling Engine · Built for Novig</div>", unsafe_allow_html=True)

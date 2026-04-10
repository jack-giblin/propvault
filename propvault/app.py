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
  .block-container { padding: 2rem 2.5rem !important; max-width: 900px !important; margin: 0 auto; }

  /* STRATEGY GUIDE - BIG & BOLD VERSION */
  .guide-container {
    background: linear-gradient(180deg, #161e28 0%, #131920 100%);
    border: 2px solid #1e2a38;
    border-radius: 24px;
    padding: 32px;
    margin-bottom: 32px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  }
  .guide-title { 
    font-size: 28px; 
    font-weight: 900; 
    color: #f8fafc; 
    margin-bottom: 12px; 
    letter-spacing: -0.5px;
  }
  .guide-text { 
    font-size: 16px; 
    color: #94a3b8; 
    line-height: 1.6; 
    margin-bottom: 24px;
    max-width: 800px;
  }
  .legend-row { 
    display: flex; 
    gap: 16px; 
    flex-wrap: wrap; 
  }
  .legend-item { 
    display: flex; 
    flex-direction: column;
    gap: 8px;
    padding: 16px 24px;
    background: #1e293b;
    border-radius: 16px;
    border: 1px solid #334155;
    flex: 1;
    min-width: 180px;
  }
  .legend-label { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
  .legend-desc  { font-size: 15px; font-weight: 700; color: #f1f5f9; }

  /* HEADER */
  .pv-header {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px;
  }
  .pv-logo-text { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -1px; }

  /* CARDS */
  .bet-card {
    background: #131920; border: 1px solid #1e2a38;
    border-radius: 20px; padding: 24px;
    margin-bottom: 16px; display: flex; align-items: center; gap: 24px;
  }
  .bet-side { font-size: 20px; font-weight: 800; color: #f1f5f9; }
  .ev-value { font-size: 36px; font-weight: 900; }

  .stButton > button {
    height: 50px !important;
    background: #7dd3fc22 !important;
    border: 2px solid #7dd3fc55 !important;
    color: #7dd3fc !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    border-radius: 14px !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="pv-header">
  <div style="display: flex; align-items: center; gap: 16px;">
    <div style="font-size: 40px;">🦄</div>
    <div class="pv-logo-text">PropVault</div>
  </div>
  <div style="color: #64748b; font-weight: 600; font-size: 14px;">LIVE DATA ENGINE</div>
</div>
""", unsafe_allow_html=True)

# ── Strategy Guide (New High-Visibility Version) ──────────────────────────────

st.markdown("""
<div class="guide-container">
    <div class="guide-title">🚀 Betting Strategy & Tier Guide</div>
    <div class="guide-text">
        Our engine identifies discrepancies by comparing <b>Pinnacle Sharp Liquidity</b> against <b>Novig Lines</b>. 
        Higher EV% represents a larger mathematical error by the sportsbook.
    </div>
    <div class="legend-row">
        <div class="legend-item" style="border-top: 4px solid #94a3b8;">
            <div class="legend-label" style="color:#94a3b8;">Standard Edge</div>
            <div class="legend-desc">2% - 5% EV</div>
        </div>
        <div class="legend-item" style="border-top: 4px solid #facc15;">
            <div class="legend-label" style="color:#facc15;">Premium Edge</div>
            <div class="legend-desc">5% - 7% EV</div>
        </div>
        <div class="legend-item" style="border-top: 4px solid #7dd3fc; background: #0f172a;">
            <div class="legend-label" style="color:#7dd3fc;">🦄 The Unicorn</div>
            <div class="legend-desc">7% + EV Outlier</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── API Logic ─────────────────────────────────────────────────────────────────

def get_api_key():
    try: return st.secrets["ODDS_API_KEY"]
    except: return os.getenv("ODDS_API_KEY", "")

api_key = get_api_key()

if not api_key:
    st.warning("Set your API Key to begin.")
    st.stop()

# ── Data Fetching ────────────────────────────────────────────────────────────

if "bets" not in st.session_state:
    st.session_state["bets"] = []
    st.session_state["fetched_at"] = None

col_ref, _ = st.columns([2.5, 3.5])
with col_ref:
    refresh = st.button("🦄 HUNT FOR UNICORNS")

if refresh or st.session_state["fetched_at"] is None:
    with st.spinner("Calculating probability distributions..."):
        bets, errors = find_ev_bets(api_key)
        st.session_state["bets"] = bets
        st.session_state["fetched_at"] = time.time()

bets = st.session_state.get("bets", [])

# ── Render Cards ──────────────────────────────────────────────────────────────

if not bets:
    st.markdown("<div style='text-align:center; padding:50px; color:#475569;'>Searching for market anomalies...</div>", unsafe_allow_html=True)
else:
    for bet in bets:
        ev = bet["EV %"]
        color = "#7dd3fc" if ev >= 7 else "#facc15" if ev >= 5 else "#94a3b8"
        bg = "rgba(125, 211, 252, 0.1)" if ev >= 7 else "transparent"
        label = "🦄 UNICORN" if ev >= 7 else "🔥 PREMIUM" if ev >= 5 else "📊 STANDARD"

        st.markdown(f"""
        <div class="bet-card" style="border-left: 6px solid {color}; background: {bg};">
          <div style="flex: 1;">
            <div style="color: {color}; font-weight: 900; font-size: 12px; margin-bottom: 8px; letter-spacing: 1px;">{label}</div>
            <div class="bet-side">{bet["Side"]}</div>
            <div style="color: #64748b; font-size: 14px; margin-top: 4px;">{bet["Game"]} · {bet["Market"]}</div>
            <div style="margin-top: 16px; display: flex; align-items: center; gap: 12px;">
                <span style="background: #22c55e22; color: #4ade80; padding: 6px 12px; border-radius: 8px; font-weight: 800; font-size: 18px;">{bet["Novig Odds"]}</span>
                <span style="color: #475569; font-size: 12px; font-weight: 600;">vs Fair {bet["Fair Odds"]}</span>
            </div>
          </div>
          <div style="text-align: right;">
            <div class="ev-value" style="color: {color};">+{ev}%</div>
            <div style="color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase;">Expected Value</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

import os
import time
import streamlit as st
from ev_engine import find_ev_bets

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# ── CUSTOM UI (CSS) ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0d1117 !important;
    font-family: 'Inter', sans-serif !important;
  }
  .block-container { padding: 2rem 2.5rem !important; max-width: 900px !important; margin: 0 auto; }

  div.stButton { text-align: center; display: flex; justify-content: center; margin: 30px 0; }
  div.stButton > button {
    width: 380px !important; height: 64px !important;
    background: #131920 !important; border: 2px solid #7dd3fc !important;
    border-radius: 16px !important; color: #7dd3fc !important;
    font-weight: 900 !important; font-size: 18px !important;
    text-transform: uppercase !important; letter-spacing: 1px !important;
    transition: all 0.3s ease;
  }
  div.stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 25px rgba(125, 211, 252, 0.3); }

  .guide-container { background: #131920; border: 1px solid #1e2a38; border-radius: 24px; padding: 32px; margin-bottom: 20px; }
  .legend-item { background: #1e293b; border-radius: 16px; padding: 16px; flex: 1; min-width: 150px; border: 1px solid #334155; text-align: center; }
  .bet-card { background: #131920; border: 1px solid #1e2a38; border-radius: 20px; padding: 24px; margin-bottom: 16px; display: flex; align-items: center; gap: 24px; }
  .bet-side { font-size: 20px; font-weight: 800; color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# ── LOGIC & STATE ────────────────────────────────────────────────────────────
api_key = os.environ.get("ODDS_API_KEY", "")

@st.cache_data(ttl=120, show_spinner=False)
def cached_hunt(key):
    return find_ev_bets(key.strip() if key else "")

if "bets" not in st.session_state: st.session_state["bets"] = []
if "last_run" not in st.session_state: st.session_state["last_run"] = None

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 30px;">
        <h1 style="background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 48px; font-weight: 900; margin: 0;">PropVault</h1>
    </div>
""", unsafe_allow_html=True)

# ── STRATEGY GUIDE ───────────────────────────────────────────────────────────
st.markdown("""
<div class="guide-container">
    <div style="font-size: 24px; font-weight: 800; color: #fff; margin-bottom: 10px;">🚀 Strategy & Tier Guide</div>
    <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 25px;">
        <div class="legend-item" style="border-top: 4px solid #94a3b8;"><div style="color:#94a3b8; font-size:12px; font-weight:800;">STANDARD</div><div>2% - 5% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #facc15;"><div style="color:#facc15; font-size:12px; font-weight:800;">PREMIUM</div><div>5% - 7% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #7dd3fc;"><div style="color:#7dd3fc; font-size:12px; font-weight:800;">🦄 UNICORN</div><div>7%+ EV</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── PRO TIPS ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #ef4444; margin-bottom: 25px;">
    <div style="font-size: 18px; font-weight: 800; color: #ef4444; margin-bottom: 10px;">📉 THE "ANTI-PUBLIC" STRATEGY</div>
    <div style="font-size: 14px; color: #e2e8f0;">Focus on <b>Unders</b>. Public bias inflates Over prices. "There are more ways to lose with an Over than an Under."</div>
</div>
""", unsafe_allow_html=True)

# ── THE BUTTON ───────────────────────────────────────────────────────────────
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    if st.button("🦄 HUNT FOR UNICORNS"):
        with st.spinner("Analyzing Markets..."):
            res, errs = cached_hunt(api_key)
            st.session_state["bets"] = res
            st.session_state["last_run"] = time.strftime("%H:%M:%S")
            if errs:
                for e in errs: st.error(e)

# ── RESULTS ──────────────────────────────────────────────────────────────────
if st.session_state["last_run"]:
    st.markdown(f"<div style='text-align:center; color:#475569; font-size:12px; margin-bottom:20px;'>Last Update: {st.session_state['last_run']}</div>", unsafe_allow_html=True)

bets = st.session_state["bets"]

if not bets:
    st.markdown("<div style='text-align:center; padding:60px; color:#334155;'>Click the button to scan for market anomalies.</div>", unsafe_allow_html=True)
else:
    for bet in bets:
        ev = bet["EV %"]
        color = "#7dd3fc" if ev >= 7 else "#facc15" if ev >= 5 else "#94a3b8"
        label = "🦄 UNICORN" if ev >= 7 else "🔥 PREMIUM" if ev >= 5 else "📊 STANDARD"

        st.markdown(f"""
        <div class="bet-card" style="border-left: 6px solid {color};">
          <div style="flex: 1;">
            <div style="color: {color}; font-weight: 900; font-size: 12px; margin-bottom: 4px;">{label}</div>
            <div class="bet-side">{bet["Side"]}</div>
            <div style="color: #64748b; font-size: 14px;">{bet["Game"]} · {bet["Market"]}</div>
            <div style="margin-top: 12px; display: flex; align-items: center; gap: 10px;">
                <span style="background: #22c55e22; color: #4ade80; padding: 4px 10px; border-radius: 6px; font-weight: 800;">{bet["Target Odds"]}</span>
                <span style="color: #475569; font-size: 12px;">vs Fair {bet["Fair Odds"]}</span>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 32px; font-weight: 900; color: {color};">+{ev}%</div>
            <div style="color: #64748b; font-size: 11px; font-weight: 700;">EXPECTED VALUE</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

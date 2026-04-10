import os
import time
import streamlit as st
from ev_engine import find_ev_bets

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# ── DONATION ─────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="display: flex; justify-content: flex-end; padding-top: 60px; margin-bottom: -45px;">
        <a href="https://www.buymeacoffee.com/notjxck" target="_blank" style="text-decoration: none;">
            <div style="color: #ffffff; font-size: 13px; border: 1px solid #7dd3fc; padding: 10px 20px; border-radius: 25px; background: rgba(125, 211, 252, 0.1); font-weight: 800; letter-spacing: 0.5px; transition: 0.3s; box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);">
                🍺 Buy me a beer to support the server
            </div>
        </a>
    </div>
""", unsafe_allow_html=True)

# ── CSS (Full Styles Restored) ───────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
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
    box-shadow: 0 0 15px rgba(125, 211, 252, 0.1); transition: all 0.3s ease;
  }
  div.stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 25px rgba(125, 211, 252, 0.3); }
  .guide-container { background: #131920; border: 1px solid #1e2a38; border-radius: 24px; padding: 32px; margin-bottom: 20px; }
  .legend-item { background: #1e293b; border-radius: 16px; padding: 16px; flex: 1; min-width: 150px; border: 1px solid #334155; text-align: center; }
  .bet-card { background: #131920; border: 1px solid #1e2a38; border-radius: 20px; padding: 24px; margin-bottom: 16px; display: flex; align-items: center; gap: 24px; }
  .bet-side { font-size: 20px; font-weight: 800; color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# ── LOGIC ────────────────────────────────────────────────────────────────────
api_key = os.environ.get("ODDS_API_KEY", "")

@st.cache_data(ttl=120, show_spinner=False)
def cached_hunt(key_to_use):
    return find_ev_bets(key_to_use.strip() if key_to_use else "")

if "bets" not in st.session_state: st.session_state["bets"] = []
if "last_run" not in st.session_state: st.session_state["last_run"] = None

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 30px;">
        <img src="https://img.icons8.com/fluency/96/unicorn.png" style="width: 65px; height: 65px;">
        <h1 style="background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 48px; font-weight: 900; letter-spacing: -1.5px; margin: 0;">PropVault</h1>
    </div>
""", unsafe_allow_html=True)

# ── STRATEGY GUIDE ───────────────────────────────────────────────────────────
st.markdown("""
<div class="guide-container">
    <div style="font-size: 24px; font-weight: 800; color: #fff; margin-bottom: 10px;">🚀 Strategy & Tier Guide</div>
    <div style="color: #f1f5f9; margin-bottom: 24px;">PropVault identifies discrepancies by cross-referencing Pinnacle’s sharp-market liquidity against Draftkings' live lines.</div>
    <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 25px;">
        <div class="legend-item" style="border-top: 4px solid #94a3b8;"><div style="color:#94a3b8; font-size:12px; font-weight:800;">STANDARD</div><div style="font-weight:700;">2% - 5% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #facc15;"><div style="color:#facc15; font-size:12px; font-weight:800;">PREMIUM</div><div style="font-weight:700;">5% - 7% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #7dd3fc;"><div style="color:#7dd3fc; font-size:12px; font-weight:800;">🦄 UNICORN</div><div style="font-weight:700;">7%+ EV</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── FULL PRO TIPS (The "Under" Bias Restored) ────────────────────────────────
st.markdown("""
<div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #ef4444; margin-bottom: 25px;">
    <div style="font-size: 18px; font-weight: 800; color: #ef4444; margin-bottom: 15px; letter-spacing: 1px; text-transform: uppercase;">📉 THE "ANTI-PUBLIC" STRATEGY</div>
    <div style="font-size: 15px; color: #e2e8f0; line-height: 1.6;">
        <p style="margin-bottom: 12px;"><span style="font-weight: 800; color: #fff;">1. The "Fun" Tax:</span> "Overs" carry a fun tax. Books bake in juice because people want to cheer for points. The <b>Under</b> exploits this.</p>
        <p style="margin-bottom: 12px;"><span style="font-weight: 800; color: #fff;">2. One Path vs. Ten:</span> To hit an Over, everything must go perfectly. An <b>Under</b> wins if there is an injury, blowout, foul trouble, or a bad night.</p>
        <p style="margin-bottom: 12px;"><span style="font-weight: 800; color: #fff;">3. Pitcher Strikeout Unders:</span> A pitcher hits an Under if they get shelled or hit a pitch count. Over requires flawless play for 6+ innings.</p>
    </div>
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
    st.markdown("<div style='text-align:center; padding:60px; color:#334155;'>No anomalies found. Try again in a few minutes.</div>", unsafe_allow_html=True)
else:
    for bet in bets:
        ev = bet["EV %"]
        color = "#7dd3fc" if ev >= 7 else "#facc15" if ev >= 5 else "#94a3b8"
        bg = "rgba(125, 211, 252, 0.05)" if ev >= 7 else "transparent"
        label = "🦄 UNICORN" if ev >= 7 else "🔥 PREMIUM" if ev >= 5 else "📊 STANDARD"

        st.markdown(f"""
        <div class="bet-card" style="border-left: 6px solid {color}; background: {bg};">
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
            <div style="color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase;">Expected Value</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

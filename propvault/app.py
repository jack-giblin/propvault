import os
import time
import streamlit as st
from ev_engine import find_ev_bets

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# ── CSS (Now includes centering and button heft) ─────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0d1117 !important;
    font-family: 'Inter', sans-serif !important;
  }
  .block-container { padding: 2rem 2.5rem !important; max-width: 900px !important; margin: 0 auto; }

  /* CENTERING THE BUTTON CONTAINER */
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

  /* STRATEGY GUIDE */
  .guide-container {
    background: #131920; border: 1px solid #1e2a38;
    border-radius: 24px; padding: 32px; margin-bottom: 20px;
  }
  .legend-item { 
    background: #1e293b; border-radius: 16px; padding: 16px; flex: 1; min-width: 150px;
    border: 1px solid #334155; text-align: center;
  }
  
  /* CARDS */
  .bet-card {
    background: #131920; border: 1px solid #1e2a38; border-radius: 20px;
    padding: 24px; margin-bottom: 16px; display: flex; align-items: center; gap: 24px;
  }
  .bet-side { font-size: 20px; font-weight: 800; color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# ── LOGIC & STATE ────────────────────────────────────────────────────────────
def get_api_key():
    # We REMOVED os.getenv to stop it from pulling that old ghost key
    key = st.secrets.get("ODDS_API_KEY", "")
    return key.strip() if key else ""

api_key = get_api_key()

# Initialize session state so data persists
if "bets" not in st.session_state:
    st.session_state["bets"] = []
if "last_run" not in st.session_state:
    st.session_state["last_run"] = None

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
    <div style="font-size: 40px;">🦄</div>
    <div style="font-size: 32px; font-weight: 900; color: #fff;">PropVault</div>
</div>
""", unsafe_allow_html=True)

# ── STRATEGY GUIDE ───────────────────────────────────────────────────────────
st.markdown("""
<div class="guide-container">
    <div style="font-size: 24px; font-weight: 800; color: #fff; margin-bottom: 10px;">🚀 Strategy & Tier Guide</div>
    <div style="color: #94a3b8; margin-bottom: 24px;">PropVault identifies price discrepancies by cross-referencing Pinnacle’s sharp-market liquidity against Novig’s live lines. When the "Fair Value" price is lower than the available odds, you have a mathematical edge.</div>
    <div style="display: flex; gap: 16px; flex-wrap: wrap;">
        <div class="legend-item" style="border-top: 4px solid #94a3b8;"><div style="color:#94a3b8; font-size:12px; font-weight:800;">STANDARD</div><div style="font-weight:700;">2% - 5% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #facc15;"><div style="color:#facc15; font-size:12px; font-weight:800;">PREMIUM</div><div style="font-weight:700;">5% - 7% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #7dd3fc;"><div style="color:#7dd3fc; font-size:12px; font-weight:800;">🦄 UNICORN</div><div style="font-weight:700;">7%+ EV</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 7. PRO TIPS (The "Under" Bias) ──────────────────────────────────────────
st.markdown("""
<div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border-left: 4px solid #ef4444; margin-bottom: 20px;">
    <div style="font-size: 16px; font-weight: 700; color: #ef4444; margin-bottom: 10px;">📉 The "Anti-Public" Strategy (Reddit Analysis)</div>
    <div style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
        <p style="margin-bottom: 8px;"><b>1. Overs are a Trap:</b> Data on 4,000+ picks shows "Overs" have a <b>-2.26% ROI</b>. The public bets them because "Overs are fun." Books know this and inflate the numbers. <b>Unders</b> showed a <b>+3.33% ROI</b> because they aren't "fun" and the value is ignored.</p>
        <p style="margin-bottom: 8px;"><b>2. More Ways to Win:</b> An "Over" requires a perfect game. An <b>Under</b> wins if there is an injury, foul trouble, a blowout, a coaching change, or just a bad shooting day. <i>"There are more ways to lose with an Over than an Under."</i></p>
        <p style="margin-bottom: 8px;"><b>3. The "Jontay" Factor:</b> Books hate Unders so much they've started removing them or juicing them to be "unattractive." When the scanner finds a <b>7% Edge on an Under</b>, it's a mistake the book didn't want you to find.</p>
        <p style="margin-bottom: 8px;"><b>4. Basketball & Hockey:</b> These sports showed the <b>worst results</b> for "Over" bettors. If you see a high-EV Under in the NBA, that is the gold standard of this strategy.</p>
        <p style="font-style: italic; color: #94a3b8; font-size: 12px; border-top: 1px solid #444; padding-top: 8px; margin-top: 8px;">"Life’s too short to bet the Under" is a motto created by sportsbooks to keep you betting on their terms.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── THE BUTTON (Centered with Spacers) ───────────────────────────────────────
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    if st.button("🦄 HUNT FOR UNICORNS"):
        with st.spinner("Analyzing Markets..."):
            results, errors = find_ev_bets(api_key)
            st.session_state["bets"] = results
            st.session_state["last_run"] = time.strftime("%H:%M:%S")
            if errors:
                for err in errors: st.error(err)

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
        bg = "rgba(125, 211, 252, 0.05)" if ev >= 7 else "transparent"
        label = "🦄 UNICORN" if ev >= 7 else "🔥 PREMIUM" if ev >= 5 else "📊 STANDARD"

        st.markdown(f"""
        <div class="bet-card" style="border-left: 6px solid {color}; background: {bg};">
          <div style="flex: 1;">
            <div style="color: {color}; font-weight: 900; font-size: 12px; margin-bottom: 4px;">{label}</div>
            <div class="bet-side">{bet["Side"]}</div>
            <div style="color: #64748b; font-size: 14px;">{bet["Game"]} · {bet["Market"]}</div>
            <div style="margin-top: 12px; display: flex; align-items: center; gap: 10px;">
                <span style="background: #22c55e22; color: #4ade80; padding: 4px 10px; border-radius: 6px; font-weight: 800;">{bet["Novig Odds"]}</span>
                <span style="color: #475569; font-size: 12px;">vs Fair {bet["Fair Odds"]}</span>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 32px; font-weight: 900; color: {color};">+{ev}%</div>
            <div style="color: #64748b; font-size: 11px; font-weight: 700; text-transform: uppercase;">Expected Value</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

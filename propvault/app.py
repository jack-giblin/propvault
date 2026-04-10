import os
import time
import streamlit as st
from ev_engine import find_ev_bets

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

st.markdown("""
    <div style="
        display: flex; 
        justify-content: flex-end; 
        padding-top: 60px; 
        margin-bottom: -45px;
    ">
        <a href="https://www.buymeacoffee.com/notjxck" target="_blank" style="text-decoration: none;">
            <div style="
                color: #ffffff; 
                font-size: 13px; 
                border: 1px solid #7dd3fc; 
                padding: 10px 20px; 
                border-radius: 25px; 
                background: rgba(125, 211, 252, 0.1);
                font-weight: 800;
                letter-spacing: 0.5px;
                transition: 0.3s;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
            ">
                🍺 Please buy me a beer to support the server
            </div>
        </a>
    </div>
""", unsafe_allow_html=True)

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
    # 1. Try pulling from Railway Variables first
    key = os.environ.get("ODDS_API_KEY")
    
    # 2. If Railway variable is missing, safely try secrets
    if not key:
        try:
            # Using .get and catching all Exceptions prevents the "No secrets found" crash
            key = st.secrets.get("ODDS_API_KEY", "")
        except Exception:
            key = ""
            
    return key.strip() if key else ""

# This will now return an empty string instead of crashing the site
api_key = get_api_key()

# ⚡ THIS IS THE MAGIC PART: CACHING
# We set the TTL to 120 seconds (2 minutes). 
# If anyone clicks the button within 5 mins of the last hit, 
# it pulls the result from memory instead of the API.
@st.cache_data(ttl=120, show_spinner=False)
def cached_hunt(api_key):
    results, errors = find_ev_bets(api_key)
    return results, errors, time.strftime("%H:%M:%S")

# Initialize session state so data persists
if "bets" not in st.session_state:
    st.session_state["bets"] = []
if "last_run" not in st.session_state:
    st.session_state["last_run"] = None

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 30px;">
        <img src="https://img.icons8.com/fluency/96/unicorn.png" 
             style="width: 65px; height: 65px; filter: drop-shadow(0 0 10px rgba(125, 211, 252, 0.4));">
        <h1 style="
            background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'Inter', sans-serif;
            font-size: 48px;
            font-weight: 900;
            letter-spacing: -1.5px;
            margin: 0;
        ">
            PropVault
        </h1>
    </div>
""", unsafe_allow_html=True)


# ── STRATEGY GUIDE ───────────────────────────────────────────────────────────
st.markdown("""
<div class="guide-container">
    <div style="font-size: 24px; font-weight: 800; color: #fff; margin-bottom: 10px;">🚀 Strategy & Tier Guide</div>
    <div style="color: #f1f5f9; margin-bottom: 24px;">PropVault identifies price discrepancies by cross-referencing Pinnacle’s sharp-market liquidity against Novig’s live lines. When the "Fair Value" price is lower than the available odds, you have a mathematical edge.</div>
    <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 25px;">
        <div class="legend-item" style="border-top: 4px solid #94a3b8;"><div style="color:#94a3b8; font-size:12px; font-weight:800;">STANDARD</div><div style="font-weight:700;">2% - 5% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #facc15;"><div style="color:#facc15; font-size:12px; font-weight:800;">PREMIUM</div><div style="font-weight:700;">5% - 7% EV</div></div>
        <div class="legend-item" style="border-top: 4px solid #7dd3fc;"><div style="color:#7dd3fc; font-size:12px; font-weight:800;">🦄 UNICORN</div><div style="font-weight:700;">7%+ EV</div></div>
    </div>
    <div style="
        margin-top: 25px; 
        padding-top: 15px; 
        border-top: 1px solid #1e2a38; 
        font-size: 15px; 
        color: #f1f5f9; 
        line-height: 1.6;
    ">
        🔒 <i><b>PropVault Logic:</b></i> PropVault is built for sustainable growth, not chasing outliers. 
        We cap EV at 15% and Win Prob at 40% to filter out "trap" lines and low-liquidity longshots. 
        We focus on high-probability discrepancies where the math is most reliable.
    </div>
</div>
""", unsafe_allow_html=True)

# ── 7. PRO TIPS (The "Under" Bias) ──────────────────────────────────────────
st.markdown("""
<div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #ef4444; margin-bottom: 25px;">
    <div style="font-size: 18px; font-weight: 800; color: #ef4444; margin-bottom: 15px; letter-spacing: 1px; text-transform: uppercase;">📉 THE "ANTI-PUBLIC" STRATEGY</div>
    <div style="font-size: 15px; color: #e2e8f0; line-height: 1.6;">
        <p style="margin-bottom: 12px;">
            <span style="font-weight: 800; color: #fff;">1. The "Fun" Tax:</span> Data on 4,000+ picks shows "Overs" at a <span style="font-weight: 800; color: #fb7185;">-2.26% ROI</span>. The public bets them because they want a reason to cheer. Books know this and bake in "juice" that only the <span style="font-weight: 800; color: #4ade80;">Under (+3.33% ROI)</span> can exploit.
        </p>
        <p style="margin-bottom: 12px;">
            <span style="font-weight: 800; color: #fff;">2. One Path vs. Ten:</span> To hit a player "Over," everything must go perfectly. An <span style="font-weight: 800; color: #fff;">Under</span> wins if there is an injury, foul trouble, a blowout, a coaching change, or a bad shooting night. <i>"There are more ways to lose with an Over than an Under."</i>
        </p>
        <p style="margin-bottom: 12px;">
            <span style="font-weight: 800; color: #fff;">3. Pitcher Strikeout Unders:</span> This prop should not be ignored! A pitcher hits an Under if they get shelled, hit a pitch count, or the umpire has a tight zone. To hit an Over, they have to be flawless for 6+ innings. <span style="font-weight: 800; color: #7dd3fc;">Bet on the chaos.</span>
        </p>
        <p style="margin-bottom: 12px;">
            <span style="font-weight: 800; color: #fff;">4. The "Worst" Markets:</span> <span style="font-weight: 900; color: #fff;">Basketball and Hockey</span> showed the worst results for "Over" bettors. These sports are driven by streaks and rotations that the public ignores. If the scanner finds a high-EV Under in the NBA or NHL, that is the gold standard of this strategy.
        </p>
        <div style="border-top: 1px solid #444; padding-top: 10px; margin-top: 15px;">
            <span style="color: #94a3b8; font-size: 13px; font-style: italic;">
                "Life’s too short to bet the Under" is a marketing slogan designed by sportsbooks to keep you betting on their terms.
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── THE BUTTON (Centered with Spacers) ───────────────────────────────────────
_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    # Small UI touch: show how long until the next fresh data is available
    st.markdown("<div style='text-align:center; color:#475569; font-size:11px; margin-bottom:-15px;'>API Data cached for 2 mins</div>", unsafe_allow_html=True)  
    if st.button("🦄 HUNT FOR UNICORNS"):
        with st.spinner("Analyzing Markets..."):
            # Call the CACHED version of the function
            results, errors, timestamp = cached_hunt(api_key)         
            st.session_state["bets"] = results
            st.session_state["last_run"] = timestamp
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

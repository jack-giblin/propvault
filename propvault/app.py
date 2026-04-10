import os
import time
import streamlit as st
# Ensure your ev_engine.py is in the same folder!
from ev_engine import find_ev_bets

# ── 1. PAGE SETUP ───────────────────────────────────────────────────────────
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# ── 2. KEY LOADING (The "Ghost Key" Killer) ─────────────────────────────────
def get_api_key():
    # Priority 1: Streamlit Secrets (.streamlit/secrets.toml)
    # Priority 2: OS Environment Variables
    key = st.secrets.get("ODDS_API_KEY", os.getenv("ODDS_API_KEY", ""))
    
    # We strip it here to ensure no hidden spaces or newlines break the 401
    return key.strip() if key else ""

# WE ASSIGN IT HERE SO 'api_key' IS DEFINED BEFORE THE REST OF THE CODE RUNS
api_key = get_api_key()

# ── 3. CSS (Centered Button & Styling) ──────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0d1117 !important;
    font-family: 'Inter', sans-serif !important;
  }
  .block-container { padding: 2rem 2.5rem !important; max-width: 900px !important; margin: 0 auto; }

  /* THE CENTERED BUTTON */
  div.stButton { text-align: center; display: flex; justify-content: center; margin: 30px 0; }
  div.stButton > button {
    width: 380px !important; height: 64px !important;
    background: #131920 !important; border: 2px solid #7dd3fc !important;
    border-radius: 16px !important; color: #7dd3fc !important;
    font-weight: 900 !important; font-size: 18px !important;
    text-transform: uppercase !important; letter-spacing: 1px !important;
    transition: all 0.3s ease;
  }
  div.stButton > button:hover { transform: scale(1.02); border-color: #fff; color: #fff; }

  /* CARDS & GUIDE */
  .guide-container { background: #131920; border: 1px solid #1e2a38; border-radius: 24px; padding: 32px; margin-bottom: 20px; }
  .bet-card { background: #131920; border: 1px solid #1e2a38; border-radius: 20px; padding: 24px; margin-bottom: 16px; display: flex; align-items: center; gap: 24px; }
  .bet-side { font-size: 20px; font-weight: 800; color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# ── 4. STATE MANAGEMENT ─────────────────────────────────────────────────────
if "bets" not in st.session_state:
    st.session_state["bets"] = []
if "last_run" not in st.session_state:
    st.session_state["last_run"] = None

# ── 5. HEADER ───────────────────────────────────────────────────────────────
st.markdown('<div style="font-size: 32px; font-weight: 900; color: #fff; margin-bottom: 24px;">🦄 PropVault</div>', unsafe_allow_html=True)

# ── 6. STRATEGY GUIDE ───────────────────────────────────────────────────────
st.markdown("""
<div class="guide-container">
    <div style="font-size: 20px; font-weight: 800; color: #fff; margin-bottom: 15px;">🚀 Strategy Guide</div>
    <div style="display: flex; gap: 10px;">
        <div style="flex:1; border-top:3px solid #94a3b8; padding:10px; color:#94a3b8;">STANDARD (2-5%)</div>
        <div style="flex:1; border-top:3px solid #facc15; padding:10px; color:#facc15;">PREMIUM (5-7%)</div>
        <div style="flex:1; border-top:3px solid #7dd3fc; padding:10px; color:#7dd3fc;">UNICORN (7%+)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 7. THE HUNT BUTTON ──────────────────────────────────────────────────────
# Just to be safe, we'll put this in a column to give it structure
_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    # Debug info: This will help us confirm the "Ghost Key" is gone
    if api_key:
        st.caption(f"Engine Ready (Key: {api_key[:4]}...)")
    else:
        st.error("No API Key detected!")

    if st.button("🦄 HUNT FOR UNICORNS"):
        with st.spinner("Scanning Markets..."):
            # We call the engine and pass the api_key variable
            results, errors = find_ev_bets(api_key)
            st.session_state["bets"] = results
            st.session_state["last_run"] = time.strftime("%H:%M:%S")
            
            if errors:
                for err in errors:
                    st.sidebar.error(err)

# ── 8. DISPLAY RESULTS ──────────────────────────────────────────────────────
if st.session_state["last_run"]:
    st.markdown(f"<p style='text-align:center; color:#475569;'>Last Scan: {st.session_state['last_run']}</p>", unsafe_allow_html=True)

bets = st.session_state["bets"]

if not bets:
    st.markdown("<p style='text-align:center; padding:50px; color:#475569;'>No edges found yet. Hit the button to start the hunt.</p>", unsafe_allow_html=True)
else:
    for bet in bets:
        ev = bet["EV %"]
        color = "#7dd3fc" if ev >= 7 else "#facc15" if ev >= 5 else "#94a3b8"
        label = "UNICORN" if ev >= 7 else "PREMIUM" if ev >= 5 else "STANDARD"
        
        st.markdown(f"""
        <div class="bet-card" style="border-left: 5px solid {color};">
            <div style="flex:1;">
                <div style="color:{color}; font-weight:900; font-size:12px;">{label}</div>
                <div class="bet-side">{bet['Side']}</div>
                <div style="color:#64748b; font-size:14px;">{bet['Game']} · {bet['Market']}</div>
                <div style="margin-top:10px;">
                    <span style="background:#22c55e22; color:#4ade80; padding:4px 8px; border-radius:5px;">{bet['Novig Odds']}</span>
                    <span style="color:#475569; font-size:12px; margin-left:10px;">Fair: {bet['Fair Odds']}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:28px; font-weight:900; color:{color};">+{ev}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

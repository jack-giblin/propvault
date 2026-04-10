"""
PropVault — +EV Engine
Streamlit frontend. Run with: streamlit run app.py
"""

import os
import time
import streamlit as st
from ev_engine import find_ev_bets, MIN_EV, fmt_odds

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PropVault · +EV Engine",
    page_icon="💰",
    layout="centered",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* Global */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117 !important;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stSidebar"] { background: #0a0e14; border-right: 1px solid #1e2533; }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* Cards */
  .bet-card {
    background: #131920;
    border: 1px solid #1e2a38;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }
  .bet-left { display: flex; align-items: center; gap: 14px; }
  .sport-icon {
    width: 44px; height: 44px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
  }
  .mlb-icon { background: #1e3a5f; }
  .nba-icon { background: #3b1f1f; }
  .bet-side   { font-size: 15px; font-weight: 700; color: #f1f5f9; margin-bottom: 3px; }
  .bet-meta   { font-size: 12px; color: #7a8fa8; margin-bottom: 6px; }
  .bet-odds   { display: flex; align-items: center; gap: 8px; }
  .odds-novig { font-size: 13px; font-weight: 700; }
  .odds-pos   { color: #4ade80; }
  .odds-neg   { color: #cbd5e1; }
  .odds-label { font-size: 11px; color: #64748b; }
  .odds-fair  { font-size: 12px; color: #8899aa; }
  .bet-right  { text-align: right; flex-shrink: 0; }
  .ev-value   { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .ev-label   { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
  .rank-badge {
    display: inline-block; font-size: 9px; font-weight: 600;
    color: #4a9060; background: #0f2018; border-radius: 4px;
    padding: 2px 7px; letter-spacing: 0.5px; margin-top: 6px;
  }

  /* Summary bar */
  .summary-bar {
    display: flex; background: #0a0e14;
    border: 1px solid #1e2533; border-radius: 12px;
    margin-bottom: 16px; overflow: hidden;
  }
  .summary-cell {
    flex: 1; text-align: center; padding: 14px 8px;
    border-right: 1px solid #1e2533;
  }
  .summary-cell:last-child { border-right: none; }
  .summary-val   { font-size: 22px; font-weight: 700; }
  .summary-green { color: #22c55e; }
  .summary-white { color: #e2e8f0; }
  .summary-lbl   { font-size: 10px; color: #7a8fa8; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }

  /* Live badge */
  .live-badge {
    display: inline-block; background: #22c55e22;
    border: 1px solid #22c55e44; border-radius: 20px;
    padding: 3px 12px; font-size: 11px; font-weight: 600;
    color: #22c55e; letter-spacing: 0.5px;
  }

  /* Footer */
  .footer {
    text-align: center; font-size: 11px; color: #4a6070;
    letter-spacing: 0.5px; margin-top: 24px;
  }

  /* Error box */
  .error-box {
    background: #1f0f0f; border: 1px solid #7f1d1d;
    border-radius: 10px; padding: 12px 16px;
    font-size: 12px; color: #fca5a5; margin-bottom: 12px;
  }
</style>
""", unsafe_allow_html=True)


# ── API key ───────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    """Resolve API key: Streamlit secrets → env var → sidebar input."""
    # 1. Streamlit Cloud secrets (set via app dashboard)
    try:
        return st.secrets["ODDS_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    # 2. Environment variable (local .env or host env)
    key = os.getenv("ODDS_API_KEY", "")
    if key:
        return key
    # 3. Sidebar manual entry (fallback for demos)
    return st.session_state.get("manual_api_key", "")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    api_key = get_api_key()
    if not api_key:
        manual = st.text_input(
            "Odds API Key",
            type="password",
            placeholder="Paste your key here",
            help="Get a free key at the-odds-api.com",
        )
        if manual:
            st.session_state["manual_api_key"] = manual
            api_key = manual

    st.markdown("---")
    st.markdown("""
**How it works**

1. Pulls Pinnacle (sharp) + Novig lines from The Odds API
2. Strips vig from Pinnacle via additive devig
3. Compares fair prob against Novig's price
4. Surfaces any bet where Novig gives you an edge

**Edge formula**
`EV% = (fair_prob × decimal_odds) − 1`
    """)
    st.markdown("---")
    st.markdown(f"<span style='color:#4a6070;font-size:11px'>Min EV threshold: {MIN_EV}%</span>", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("## 💰 PropVault")
    st.markdown("<p style='color:#8899aa;margin-top:-12px;font-size:14px'>+EV bets on Novig, sharp-priced against Pinnacle</p>", unsafe_allow_html=True)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<span class='live-badge'>LIVE</span>", unsafe_allow_html=True)


# ── Fetch ─────────────────────────────────────────────────────────────────────

if not api_key:
    st.warning("Add your Odds API key in the sidebar to get started.")
    st.stop()

refresh = st.button("🔄 Refresh", use_container_width=False)

if "bets" not in st.session_state or refresh:
    with st.spinner("Scanning for +EV bets…"):
        bets, errors = find_ev_bets(api_key)
        st.session_state["bets"]   = bets
        st.session_state["errors"] = errors
        st.session_state["fetched_at"] = time.strftime("%I:%M:%S %p")

bets   = st.session_state.get("bets", [])
errors = st.session_state.get("errors", [])
fetched_at = st.session_state.get("fetched_at", "")

if fetched_at:
    st.markdown(f"<p style='color:#3a5060;font-size:11px;margin-bottom:8px'>Last updated {fetched_at}</p>", unsafe_allow_html=True)


# ── Errors ────────────────────────────────────────────────────────────────────

for err in errors:
    st.markdown(f"<div class='error-box'>⚠️ {err}</div>", unsafe_allow_html=True)


# ── Summary bar ───────────────────────────────────────────────────────────────

avg_ev = round(sum(b["EV %"] for b in bets) / len(bets), 1) if bets else 0.0
top_ev = bets[0]["EV %"] if bets else 0.0

st.markdown(f"""
<div class="summary-bar">
  <div class="summary-cell">
    <div class="summary-val summary-green">{len(bets)}</div>
    <div class="summary-lbl">Bets Found</div>
  </div>
  <div class="summary-cell">
    <div class="summary-val summary-white">+{avg_ev}%</div>
    <div class="summary-lbl">Avg EV</div>
  </div>
  <div class="summary-cell">
    <div class="summary-val summary-green">{"+" + str(top_ev) + "%" if bets else "—"}</div>
    <div class="summary-lbl">Top EV</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Bet cards ─────────────────────────────────────────────────────────────────

if not bets:
    st.markdown("<p style='text-align:center;color:#64748b;padding:40px 0'>No +EV bets above 1.5% right now. Try refreshing.</p>", unsafe_allow_html=True)
else:
    for i, bet in enumerate(bets):
        sport       = bet["Sport"]
        icon_class  = "mlb-icon" if sport == "MLB" else "nba-icon"
        icon_emoji  = "⚾" if sport == "MLB" else "🏀"
        ev          = bet["EV %"]
        ev_color    = "#4ade80" if ev >= 8 else "#facc15" if ev >= 5 else "#fb923c" if ev >= 3 else "#94a3b8"
        novig_raw   = bet["Novig Odds"]
        odds_class  = "odds-pos" if novig_raw.startswith("+") else "odds-neg"

        st.markdown(f"""
        <div class="bet-card">
          <div class="bet-left">
            <div class="sport-icon {icon_class}">{icon_emoji}</div>
            <div>
              <div class="bet-side">{bet["Side"]}</div>
              <div class="bet-meta">{bet["Game"]} · {bet["Market"]} · {sport}</div>
              <div class="bet-odds">
                <span class="odds-novig {odds_class}">{novig_raw}</span>
                <span class="odds-label">vs fair</span>
                <span class="odds-fair">{bet["Fair Odds"]}</span>
              </div>
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
<div class="footer">
  SHARP: PINNACLE &nbsp;·&nbsp; DEVIG: ADDITIVE &nbsp;·&nbsp; BOOK: NOVIG
</div>
""", unsafe_allow_html=True)

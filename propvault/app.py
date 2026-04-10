"""
PropVault — +EV Engine
Railway deployment. Run with: streamlit run app.py
"""

import os
import time
import streamlit as st
from ev_engine import find_ev_bets

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Barlow:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background-color: #080c12 !important;
  font-family: 'Barlow', sans-serif !important;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Ticker ── */
.ticker-wrap {
  width: 100%;
  background: #0d1520;
  border-bottom: 1px solid #1a2535;
  padding: 10px 0;
  overflow: hidden;
  white-space: nowrap;
}
.ticker-inner {
  display: inline-block;
  animation: ticker 30s linear infinite;
}
.ticker-inner:hover { animation-play-state: paused; }
.ticker-item {
  display: inline-block;
  margin: 0 32px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #4a6a8a;
}
.ticker-item .ticker-game { color: #8aaac8; }
.ticker-item .ticker-ev   { color: #22c55e; margin-left: 8px; }
.ticker-item .ticker-sep  { color: #1a3050; margin: 0 16px; }
@keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

/* ── Header ── */
.pv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 48px 0;
  margin-bottom: 32px;
}
.pv-brand { display: flex; align-items: center; gap: 16px; }
.pv-brand-icon {
  width: 52px; height: 52px; border-radius: 16px;
  background: linear-gradient(135deg, #1a4a8a 0%, #0d2a5a 100%);
  border: 1px solid #2a5aaa;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px;
}
.pv-brand-name {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 38px; font-weight: 900;
  color: #fff; letter-spacing: -1px;
  line-height: 1;
}
.pv-brand-tag {
  font-size: 12px; font-weight: 600;
  color: #2a5a8a; letter-spacing: 2px;
  text-transform: uppercase; margin-top: 2px;
}
.pv-live-badge {
  display: flex; align-items: center; gap: 8px;
  background: #0a1e10;
  border: 1px solid #22c55e44;
  border-radius: 24px; padding: 8px 18px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 14px; font-weight: 700;
  color: #22c55e; letter-spacing: 2px;
}
.pv-live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #22c55e;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(0.85)} }

/* ── Main content ── */
.pv-content { padding: 0 48px 48px; }

/* ── Stats row ── */
.pv-stats {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 16px; margin-bottom: 32px;
}
.pv-stat {
  background: #0d1520;
  border: 1px solid #1a2535;
  border-radius: 20px;
  padding: 24px 28px;
  position: relative; overflow: hidden;
}
.pv-stat::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.pv-stat.green::before { background: #22c55e; }
.pv-stat.blue::before  { background: #3b82f6; }
.pv-stat.gold::before  { background: #f59e0b; }
.pv-stat-num {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 44px; font-weight: 900;
  letter-spacing: -2px; line-height: 1;
  margin-bottom: 6px;
}
.pv-stat.green .pv-stat-num { color: #22c55e; }
.pv-stat.blue  .pv-stat-num { color: #7dd3fc; }
.pv-stat.gold  .pv-stat-num { color: #fbbf24; }
.pv-stat-lbl {
  font-size: 11px; font-weight: 700;
  color: #2a4060; letter-spacing: 2px; text-transform: uppercase;
}

/* ── Tier guide ── */
.pv-guide {
  background: #0d1520;
  border: 1px solid #1a2535;
  border-radius: 20px;
  padding: 28px 32px;
  margin-bottom: 32px;
}
.pv-guide-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 22px; font-weight: 800;
  color: #fff; letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.pv-guide-sub {
  font-size: 14px; color: #4a6a8a;
  margin-bottom: 24px; line-height: 1.5;
}
.pv-tiers {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}
.pv-tier {
  background: #080c12;
  border-radius: 14px; padding: 18px 20px;
  border-top: 3px solid;
  text-align: center;
}
.pv-tier.standard { border-color: #64748b; }
.pv-tier.premium  { border-color: #f59e0b; }
.pv-tier.unicorn  { border-color: #7dd3fc; }
.pv-tier-name {
  font-size: 10px; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 6px;
}
.pv-tier.standard .pv-tier-name { color: #64748b; }
.pv-tier.premium  .pv-tier-name { color: #f59e0b; }
.pv-tier.unicorn  .pv-tier-name { color: #7dd3fc; }
.pv-tier-range {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 22px; font-weight: 800; color: #fff;
}

/* ── Strategy box ── */
.pv-strategy {
  background: #0d0808;
  border: 1px solid #2a1010;
  border-left: 4px solid #ef4444;
  border-radius: 0 16px 16px 0;
  padding: 24px 28px;
  margin-bottom: 32px;
}
.pv-strategy-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 18px; font-weight: 800;
  color: #ef4444; letter-spacing: 1px;
  text-transform: uppercase; margin-bottom: 16px;
}
.pv-strategy p {
  font-size: 14px; color: #c8d8e8;
  line-height: 1.7; margin-bottom: 10px;
}
.pv-strategy p:last-child { margin-bottom: 0; }
.pv-strategy strong { color: #fff; }

/* ── Hunt button ── */
.pv-btn-wrap {
  display: flex; justify-content: center;
  margin: 36px 0;
}
div.stButton { display: flex; justify-content: center; margin: 8px 0 32px; }
div.stButton > button {
  width: 400px !important; height: 68px !important;
  background: #080c12 !important;
  border: 2px solid #7dd3fc !important;
  border-radius: 18px !important;
  color: #7dd3fc !important;
  font-family: 'Barlow Condensed', sans-serif !important;
  font-weight: 900 !important; font-size: 20px !important;
  letter-spacing: 3px !important; text-transform: uppercase !important;
  transition: all 0.25s ease !important;
}
div.stButton > button:hover {
  background: #0d1e2e !important;
  box-shadow: 0 0 30px rgba(125,211,252,0.15) !important;
  transform: translateY(-1px) !important;
}

/* ── Bet cards ── */
.pv-section-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 18px; font-weight: 800;
  color: #2a4060; letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 16px;
}
.bet-card {
  background: #0d1520;
  border: 1px solid #1a2535;
  border-radius: 20px;
  padding: 24px 28px;
  margin-bottom: 14px;
  display: flex; align-items: center; gap: 24px;
  transition: border-color 0.15s, transform 0.15s;
}
.bet-card:hover { border-color: #2a3a50; transform: translateY(-1px); }
.bet-card.unicorn { border-color: #7dd3fc33; background: #0a1828; }
.bet-card.premium { border-color: #f59e0b33; }

.sport-pill {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  width: 56px; height: 56px; border-radius: 16px;
  flex-shrink: 0; font-size: 24px;
}
.sport-pill.mlb { background: #0a1e3a; border: 1px solid #1a3a6a; }
.sport-pill.nba { background: #1a0a0a; border: 1px solid #4a1a1a; }

.bet-body { flex: 1; min-width: 0; }
.bet-tier {
  font-size: 10px; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 5px;
}
.bet-tier.unicorn { color: #7dd3fc; }
.bet-tier.premium { color: #f59e0b; }
.bet-tier.standard { color: #64748b; }
.bet-side {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 24px; font-weight: 800;
  color: #f1f5f9; letter-spacing: 0.3px;
  margin-bottom: 4px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bet-meta { font-size: 13px; color: #2a4060; margin-bottom: 12px; font-weight: 500; }
.bet-odds { display: flex; align-items: center; gap: 10px; }
.odds-pill {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 18px; font-weight: 800;
  padding: 5px 14px; border-radius: 10px;
}
.odds-pill.pos { color: #4ade80; background: #0a2a12; border: 1px solid #22c55e33; }
.odds-pill.neg { color: #93c5fd; background: #0a1428; border: 1px solid #3b82f633; }
.odds-vs   { font-size: 11px; color: #1a3050; font-weight: 600; }
.odds-fair { font-family: 'Barlow Condensed', sans-serif; font-size: 16px; color: #2a4a6a; font-weight: 700; }

.bet-right { text-align: right; flex-shrink: 0; min-width: 110px; }
.ev-num {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 42px; font-weight: 900;
  letter-spacing: -2px; line-height: 1;
}
.ev-lbl {
  font-size: 10px; font-weight: 700;
  color: #1a3050; text-transform: uppercase;
  letter-spacing: 2px; margin-top: 2px;
}

/* ── Empty / error ── */
.pv-empty {
  text-align: center; padding: 80px 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 22px; font-weight: 700;
  color: #1a2535; letter-spacing: 1px; text-transform: uppercase;
}
.pv-error {
  background: #1a0808; border: 1px solid #5a1a1a;
  border-radius: 12px; padding: 12px 18px;
  font-size: 13px; color: #fca5a5; margin-bottom: 10px;
}
.pv-updated {
  text-align: center; font-size: 12px;
  color: #1a3050; font-weight: 600;
  letter-spacing: 1px; margin-bottom: 24px;
}
.pv-footer {
  text-align: center; font-size: 11px;
  color: #0d1a28; letter-spacing: 2px;
  text-transform: uppercase; margin-top: 48px;
  padding-bottom: 32px;
}

/* ── Buy me a beer ── */
.pv-beer {
  display: flex; justify-content: flex-end;
  padding: 12px 48px 0;
}
.pv-beer a {
  color: #7dd3fc; font-size: 12px; font-weight: 700;
  border: 1px solid #1a3a5a; border-radius: 20px;
  padding: 7px 16px; text-decoration: none;
  letter-spacing: 0.5px;
  background: rgba(125,211,252,0.05);
}
</style>
""", unsafe_allow_html=True)

# ── API key ───────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    try:
        return st.secrets["ODDS_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ODDS_API_KEY", "")

api_key = get_api_key()

# ── Session state ─────────────────────────────────────────────────────────────
if "bets"       not in st.session_state: st.session_state["bets"]       = []
if "errors"     not in st.session_state: st.session_state["errors"]     = []
if "fetched_at" not in st.session_state: st.session_state["fetched_at"] = None

CACHE_SECONDS = 300  # 5 minutes

def should_refresh() -> bool:
    if st.session_state["fetched_at"] is None:
        return True
    return (time.time() - st.session_state["fetched_at"]) >= CACHE_SECONDS

def do_fetch():
    if not api_key:
        st.session_state["errors"] = ["No ODDS_API_KEY found. Set it in Railway Variables."]
        return
    bets, errors = find_ev_bets(api_key)
    st.session_state["bets"]       = bets
    st.session_state["errors"]     = errors
    st.session_state["fetched_at"] = time.time()

# Auto-refresh on first load or when cache expires
if should_refresh():
    do_fetch()

bets       = st.session_state["bets"]
errors     = st.session_state["errors"]
fetched_at = st.session_state["fetched_at"]

# ── Ticker ────────────────────────────────────────────────────────────────────
if bets:
    items_html = ""
    for b in bets:
        tier = "🦄" if b["EV %"] >= 7 else "🔥" if b["EV %"] >= 5 else "📊"
        items_html += f'<span class="ticker-item">{tier} <span class="ticker-game">{b["Side"]} — {b["Game"]}</span><span class="ticker-ev">+{b["EV %"]}% EV</span></span><span class="ticker-item ticker-sep">·</span>'
    # Duplicate for seamless loop
    ticker_html = f'<div class="ticker-wrap"><div class="ticker-inner">{items_html}{items_html}</div></div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

# ── Beer button ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="pv-beer">
  <a href="https://www.buymeacoffee.com/notjxck" target="_blank">🍺 Buy me a beer</a>
</div>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pv-header">
  <div class="pv-brand">
    <div class="pv-brand-icon">🦄</div>
    <div>
      <div class="pv-brand-name">PropVault</div>
      <div class="pv-brand-tag">Sharp Edge Finder · Novig vs Pinnacle</div>
    </div>
  </div>
  <div class="pv-live-badge">
    <div class="pv-live-dot"></div>
    LIVE
  </div>
</div>
""", unsafe_allow_html=True)

# ── Content wrapper ───────────────────────────────────────────────────────────
st.markdown('<div class="pv-content">', unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────────────────────────────────
avg_ev = round(sum(b["EV %"] for b in bets) / len(bets), 1) if bets else 0.0
top_ev = bets[0]["EV %"] if bets else 0.0
unicorns = sum(1 for b in bets if b["EV %"] >= 7)

st.markdown(f"""
<div class="pv-stats">
  <div class="pv-stat green">
    <div class="pv-stat-num">{len(bets)}</div>
    <div class="pv-stat-lbl">Edges Found</div>
  </div>
  <div class="pv-stat blue">
    <div class="pv-stat-num">+{avg_ev}%</div>
    <div class="pv-stat-lbl">Avg EV</div>
  </div>
  <div class="pv-stat gold">
    <div class="pv-stat-num">{unicorns}</div>
    <div class="pv-stat-lbl">Unicorns 🦄</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tier guide ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pv-guide">
  <div class="pv-guide-title">🚀 Strategy & Tier Guide</div>
  <div class="pv-guide-sub">PropVault identifies price discrepancies by cross-referencing Pinnacle's sharp-market liquidity against Novig's live lines. When the fair value price is lower than the available odds, you have a mathematical edge.</div>
  <div class="pv-tiers">
    <div class="pv-tier standard">
      <div class="pv-tier-name">Standard</div>
      <div class="pv-tier-range">2% – 5% EV</div>
    </div>
    <div class="pv-tier premium">
      <div class="pv-tier-name">⚡ Premium</div>
      <div class="pv-tier-range">5% – 7% EV</div>
    </div>
    <div class="pv-tier unicorn">
      <div class="pv-tier-name">🦄 Unicorn</div>
      <div class="pv-tier-range">7%+ EV</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Strategy ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pv-strategy">
  <div class="pv-strategy-title">📉 The "Anti-Public" Strategy</div>
  <p><strong>1. The "Fun" Tax:</strong> "Overs" carry a fun tax. Books bake in juice because people want to cheer for points. The <strong>Under</strong> exploits this.</p>
  <p><strong>2. One Path vs. Ten:</strong> To hit an Over, everything must go perfectly. An <strong>Under</strong> wins if there is an injury, blowout, foul trouble, or a bad night.</p>
  <p><strong>3. Pitcher Strikeout Unders:</strong> A pitcher hits an Under if they get shelled or hit a pitch count. Over requires flawless play for 6+ innings.</p>
</div>
""", unsafe_allow_html=True)

# ── Hunt button ───────────────────────────────────────────────────────────────
if st.button("🦄  HUNT FOR UNICORNS"):
    with st.spinner("Scanning markets…"):
        do_fetch()
    st.rerun()

# ── Refresh info ─────────────────────────────────────────────────────────────
if fetched_at:
    secs = int(time.time() - fetched_at)
    next_in = max(0, CACHE_SECONDS - secs)
    if secs < 10:
        upd = "Just refreshed"
    elif secs < 60:
        upd = f"Refreshed {secs}s ago · next refresh in {next_in}s"
    else:
        upd = f"Refreshed {secs//60}m ago · next refresh in {next_in//60}m {next_in%60}s"
    st.markdown(f"<div class='pv-updated'>{upd}</div>", unsafe_allow_html=True)

# ── Errors ────────────────────────────────────────────────────────────────────
for e in errors:
    st.markdown(f"<div class='pv-error'>⚠️ {e}</div>", unsafe_allow_html=True)

# ── Bet cards ─────────────────────────────────────────────────────────────────
if not bets:
    st.markdown("<div class='pv-empty'>No edges found right now — markets are tight. Check back soon.</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='pv-section-title'>Live Edges</div>", unsafe_allow_html=True)
    for bet in bets:
        ev         = bet["EV %"]
        sport      = bet["Sport"]
        tier_cls   = "unicorn" if ev >= 7 else "premium" if ev >= 5 else "standard"
        tier_lbl   = "🦄 Unicorn" if ev >= 7 else "⚡ Premium" if ev >= 5 else "📊 Standard"
        ev_color   = "#7dd3fc" if ev >= 7 else "#fbbf24" if ev >= 5 else "#64748b"
        sport_cls  = "mlb" if sport == "MLB" else "nba"
        sport_ico  = "⚾" if sport == "MLB" else "🏀"
        odds_cls   = "pos" if bet["Target Odds"].startswith("+") else "neg"
        card_cls   = f"bet-card {tier_cls}" if tier_cls != "standard" else "bet-card"

        st.markdown(f"""
        <div class="{card_cls}">
          <div class="sport-pill {sport_cls}">{sport_ico}</div>
          <div class="bet-body">
            <div class="bet-tier {tier_cls}">{tier_lbl}</div>
            <div class="bet-side">{bet["Side"]}</div>
            <div class="bet-meta">{bet["Game"]} · {bet["Market"]} · {sport}</div>
            <div class="bet-odds">
              <span class="odds-pill {odds_cls}">{bet["Target Odds"]}</span>
              <span class="odds-vs">vs fair</span>
              <span class="odds-fair">{bet["Fair Odds"]}</span>
            </div>
          </div>
          <div class="bet-right">
            <div class="ev-num" style="color:{ev_color};">+{ev}%</div>
            <div class="ev-lbl">Expected Value</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pv-footer">
  Sharp: Pinnacle &nbsp;·&nbsp; Devig: Additive &nbsp;·&nbsp; Book: Novig &nbsp;·&nbsp; Min EV: 2.0%
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

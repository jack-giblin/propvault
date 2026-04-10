"""
PropVault — +EV Engine
Railway deployment. Run: streamlit run app.py
"""

import os
import time
import streamlit as st
from ev_engine import find_ev_bets

st.set_page_config(page_title="PropVault", page_icon="🦄", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background-color: #0a0e1a !important;
  font-family: 'DM Sans', sans-serif !important;
  color: #e2e8f0;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Ticker ── */
.ticker-outer {
  background: #0d1222;
  border-bottom: 1px solid #161d30;
  padding: 11px 0;
  overflow: hidden;
  white-space: nowrap;
}
.ticker-track {
  display: inline-flex;
  animation: scroll-left 40s linear infinite;
}
.ticker-track:hover { animation-play-state: paused; }
@keyframes scroll-left {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.ticker-chip {
  display: inline-flex; align-items: center; gap: 8px;
  margin: 0 20px;
  font-size: 12px; font-weight: 600; letter-spacing: 0.3px;
  color: #3a5070;
}
.ticker-chip .t-game { color: #4a7090; }
.ticker-chip .t-ev   { color: #22c55e; font-weight: 800; }
.ticker-chip .t-dot  { color: #161d30; font-size: 16px; }

/* ── Page shell ── */
.pv-page { max-width: 860px; margin: 0 auto; padding: 32px 24px 60px; }

/* ── Header ── */
.pv-header {
  display: flex; align-items: center;
  justify-content: space-between;
  margin-bottom: 36px;
}
.pv-logo { display: flex; align-items: center; gap: 14px; }
.pv-logo-img {
  width: 54px; height: 54px; border-radius: 18px;
  overflow: hidden; flex-shrink: 0;
}
.pv-logo-img img { width: 100%; height: 100%; object-fit: cover; }
.pv-logo-name {
  font-size: 34px; font-weight: 900;
  color: #ffffff; letter-spacing: -1px; line-height: 1;
}
.pv-logo-sub {
  font-size: 12px; font-weight: 600;
  color: #2a4060; letter-spacing: 0.5px; margin-top: 3px;
}
.pv-live {
  display: flex; align-items: center; gap: 8px;
  background: #0a1e10; border: 1.5px solid #166534;
  border-radius: 100px; padding: 8px 20px;
  font-size: 13px; font-weight: 800;
  color: #22c55e; letter-spacing: 1.5px;
}
.pv-live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #22c55e;
  animation: blink 1.4s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

/* ── Stats row ── */
.pv-stats {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 12px; margin-bottom: 20px;
}
.pv-stat {
  background: #0d1525;
  border-radius: 22px;
  padding: 22px 24px;
  border: 1.5px solid #141e30;
}
.pv-stat-num {
  font-size: 40px; font-weight: 900;
  letter-spacing: -2px; line-height: 1; margin-bottom: 5px;
}
.pv-stat-lbl {
  font-size: 11px; font-weight: 700;
  letter-spacing: 1.5px; text-transform: uppercase;
  color: #1e3050;
}

/* ── Card base ── */
.card {
  background: #0d1525;
  border-radius: 22px;
  border: 1.5px solid #141e30;
  padding: 26px 28px;
  margin-bottom: 14px;
}

/* ── Guide ── */
.guide-title {
  font-size: 22px; font-weight: 800;
  color: #fff; margin-bottom: 8px;
}
.guide-sub {
  font-size: 14px; color: #3a5878;
  line-height: 1.6; margin-bottom: 22px;
}
.tiers {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 12px; margin-bottom: 18px;
}
.tier {
  background: #080c18;
  border-radius: 16px; padding: 18px 16px;
  text-align: center; border: 1.5px solid #141e30;
}
.tier-top { height: 4px; border-radius: 2px; margin-bottom: 12px; }
.tier-name {
  font-size: 10px; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 6px;
}
.tier-range {
  font-size: 20px; font-weight: 800; color: #fff;
}
.logic-box {
  background: #080c18;
  border-radius: 14px; padding: 16px 18px;
  border: 1.5px solid #141e30;
  font-size: 13px; line-height: 1.65; color: #3a5878;
}
.logic-box strong { color: #7dd3fc; font-weight: 800; }

/* ── Strategy ── */
.strategy-title {
  font-size: 16px; font-weight: 800;
  color: #ef4444; letter-spacing: 0.5px;
  text-transform: uppercase; margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}
.strategy p {
  font-size: 14px; color: #94a3b8;
  line-height: 1.7; margin-bottom: 10px;
}
.strategy p:last-child { margin-bottom: 0; }
.strategy strong { color: #e2e8f0; }
.strategy-stat {
  display: inline-block;
  background: #0a1e10; color: #4ade80;
  border-radius: 8px; padding: 2px 8px;
  font-size: 13px; font-weight: 800;
}

/* ── Hunt button ── */
div.stButton { display: flex; justify-content: center; margin: 8px 0 6px; }
div.stButton > button {
  width: 380px !important; height: 64px !important;
  background: #0d1525 !important;
  border: 2px solid #7dd3fc !important;
  border-radius: 18px !important;
  color: #7dd3fc !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 900 !important; font-size: 17px !important;
  letter-spacing: 2px !important; text-transform: uppercase !important;
  transition: all 0.2s !important;
}
div.stButton > button:hover {
  background: #111d35 !important;
  box-shadow: 0 0 28px rgba(125,211,252,0.12) !important;
}

/* ── Updated text ── */
.pv-updated {
  text-align: center; font-size: 12px;
  color: #1e3050; font-weight: 600;
  letter-spacing: 0.5px; margin: 10px 0 20px;
}

/* ── Section label ── */
.section-lbl {
  font-size: 11px; font-weight: 800;
  color: #1e3050; letter-spacing: 2px;
  text-transform: uppercase; margin-bottom: 14px;
}

/* ── Bet card ── */
.bet-card {
  background: #0d1525;
  border-radius: 22px;
  border: 1.5px solid #141e30;
  padding: 22px 24px;
  margin-bottom: 12px;
  display: flex; align-items: center; gap: 20px;
}
.bet-card.is-unicorn { border-color: #1a3a5a; background: #0a1828; }
.bet-card.is-premium { border-color: #2a2010; }

.sport-bubble {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; flex-shrink: 0;
  border: 1.5px solid;
}
.sport-bubble.mlb { background: #081428; border-color: #0e2040; }
.sport-bubble.nba { background: #180808; border-color: #280e0e; }

.bet-body { flex: 1; min-width: 0; }
.bet-tier-lbl {
  font-size: 10px; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase;
  margin-bottom: 5px;
}
.bet-side {
  font-size: 22px; font-weight: 800;
  color: #f8fafc; margin-bottom: 4px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  letter-spacing: -0.3px;
}
.bet-meta {
  font-size: 13px; color: #1e3050;
  font-weight: 500; margin-bottom: 12px;
}
.bet-odds-row { display: flex; align-items: center; gap: 10px; }
.odds-tag {
  font-size: 16px; font-weight: 800;
  padding: 5px 14px; border-radius: 12px;
}
.odds-tag.pos { color: #4ade80; background: #051410; border: 1.5px solid #0a2818; }
.odds-tag.neg { color: #93c5fd; background: #050e1c; border: 1.5px solid #0a1828; }
.odds-vs   { font-size: 11px; color: #1a2e44; font-weight: 700; }
.odds-fair { font-size: 14px; color: #2a4a6a; font-weight: 700; }

.bet-right { text-align: right; flex-shrink: 0; min-width: 110px; }
.ev-pct {
  font-size: 38px; font-weight: 900;
  letter-spacing: -2px; line-height: 1;
}
.ev-lbl {
  font-size: 10px; font-weight: 700;
  color: #1a3050; text-transform: uppercase;
  letter-spacing: 1.5px; margin-top: 3px;
}

/* ── Empty ── */
.pv-empty {
  text-align: center; padding: 70px 0;
  font-size: 16px; font-weight: 700;
  color: #1a2a3a; letter-spacing: 0.5px;
}

/* ── Error ── */
.pv-err {
  background: #160808; border: 1.5px solid #3a0a0a;
  border-radius: 14px; padding: 12px 18px;
  font-size: 13px; color: #fca5a5;
  margin-bottom: 10px; font-weight: 600;
}

/* ── Footer ── */
.pv-footer {
  text-align: center; font-size: 11px;
  color: #0d1828; letter-spacing: 2px;
  text-transform: uppercase; margin-top: 40px;
}

/* ── Beer ── */
.pv-beer {
  display: flex; justify-content: flex-end; margin-bottom: 20px;
}
.pv-beer a {
  font-size: 12px; font-weight: 700; color: #2a5a8a;
  border: 1.5px solid #141e30; border-radius: 100px;
  padding: 7px 16px; text-decoration: none;
  background: #0d1525; letter-spacing: 0.3px;
}
</style>
""", unsafe_allow_html=True)

# ── API + state ───────────────────────────────────────────────────────────────
api_key = os.environ.get("ODDS_API_KEY", "")

if "bets"       not in st.session_state: st.session_state.bets       = []
if "errors"     not in st.session_state: st.session_state.errors     = []
if "fetched_at" not in st.session_state: st.session_state.fetched_at = None

CACHE_SECS = 300

def should_refresh():
    return st.session_state.fetched_at is None or \
           (time.time() - st.session_state.fetched_at) >= CACHE_SECS

def do_fetch():
    if not api_key:
        st.session_state.errors = ["ODDS_API_KEY not set in Railway Variables."]
        return
    bets, errors = find_ev_bets(api_key)
    st.session_state.bets       = bets
    st.session_state.errors     = errors
    st.session_state.fetched_at = time.time()

if should_refresh():
    do_fetch()

bets  = st.session_state.bets
errs  = st.session_state.errors
ts    = st.session_state.fetched_at

# ── Ticker ────────────────────────────────────────────────────────────────────
if bets:
    icons = {"unicorn": "🦄", "premium": "⚡", "standard": "📊"}
    items = ""
    for b in bets:
        ico = "🦄" if b["EV %"] >= 7 else "⚡" if b["EV %"] >= 5 else "📊"
        items += f'<span class="ticker-chip">{ico} <span class="t-game">{b["Side"]} — {b["Game"]}</span><span class="t-ev">+{b["EV %"]}%</span></span><span class="ticker-chip"><span class="t-dot">·</span></span>'
    st.markdown(f'<div class="ticker-outer"><div class="ticker-track">{items}{items}</div></div>', unsafe_allow_html=True)

# ── Page shell ────────────────────────────────────────────────────────────────
st.markdown('<div class="pv-page">', unsafe_allow_html=True)

# Beer
st.markdown('<div class="pv-beer"><a href="https://www.buymeacoffee.com/notjxck" target="_blank">🍺 Buy me a beer</a></div>', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="pv-header">
  <div class="pv-logo">
    <div class="pv-logo-img">
      <img src="https://img.icons8.com/fluency/96/unicorn.png" />
    </div>
    <div>
      <div class="pv-logo-name">PropVault</div>
      <div class="pv-logo-sub">Novig vs Pinnacle · Sharp Edge Finder</div>
    </div>
  </div>
  <div class="pv-live"><div class="pv-live-dot"></div>LIVE</div>
</div>
""", unsafe_allow_html=True)

# Stats
avg_ev   = round(sum(b["EV %"] for b in bets) / len(bets), 1) if bets else 0.0
unicorns = sum(1 for b in bets if b["EV %"] >= 7)

st.markdown(f"""
<div class="pv-stats">
  <div class="pv-stat">
    <div class="pv-stat-num" style="color:#22c55e">{len(bets)}</div>
    <div class="pv-stat-lbl">Edges Found</div>
  </div>
  <div class="pv-stat">
    <div class="pv-stat-num" style="color:#7dd3fc">+{avg_ev}%</div>
    <div class="pv-stat-lbl">Avg EV</div>
  </div>
  <div class="pv-stat">
    <div class="pv-stat-num" style="color:#a78bfa">{unicorns}</div>
    <div class="pv-stat-lbl">Unicorns 🦄</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Guide
st.markdown("""
<div class="card" style="margin-bottom:14px;">
  <div class="guide-title">🚀 Strategy & Tier Guide</div>
  <div class="guide-sub">PropVault identifies price discrepancies by cross-referencing Pinnacle's sharp-market liquidity against Novig's live lines. When the "Fair Value" price is lower than the available odds, you have a mathematical edge.</div>
  <div class="tiers">
    <div class="tier">
      <div class="tier-top" style="background:#64748b;"></div>
      <div class="tier-name" style="color:#64748b;">Standard</div>
      <div class="tier-range">2% – 5% EV</div>
    </div>
    <div class="tier">
      <div class="tier-top" style="background:#f59e0b;"></div>
      <div class="tier-name" style="color:#f59e0b;">⚡ Premium</div>
      <div class="tier-range">5% – 7% EV</div>
    </div>
    <div class="tier">
      <div class="tier-top" style="background:#7dd3fc;"></div>
      <div class="tier-name" style="color:#7dd3fc;">🦄 Unicorn</div>
      <div class="tier-range">7%+ EV</div>
    </div>
  </div>
  <div class="logic-box">
    <strong>🔒 PropVault Logic:</strong> PropVault is built for sustainable growth, not chasing outliers. We cap EV at 15% and Win Prob at 40% to filter out "trap" lines and low-liquidity longshots. We focus on high-probability discrepancies where the math is most reliable.
  </div>
</div>
""", unsafe_allow_html=True)

# Strategy
st.markdown("""
<div class="card strategy" style="border-left: 3px solid #ef4444; margin-bottom:14px;">
  <div class="strategy-title">📉 The "Anti-Public" Strategy</div>
  <p>
    <strong>1. The "Fun" Tax:</strong> A community study of <span class="strategy-stat">4,344 bets</span> found Over props returned
    <span class="strategy-stat" style="color:#f87171;background:#1a0808;">-2.26% ROI</span> while Under props returned
    <span class="strategy-stat">+3.33% ROI</span> with a 56% win rate. Books bake in juice because people want to cheer for points.
  </p>
  <p><strong>2. One Path vs. Ten:</strong> To hit an Over, everything must go perfectly. An <strong>Under</strong> wins if there is an injury, blowout, foul trouble, or just a bad night.</p>
  <p><strong>3. Pitcher Strikeout Unders:</strong> A pitcher hits an Under if they get shelled or hit a pitch count. An Over requires flawless play for 6+ innings. <em>Bet on the chaos, not the perfection.</em></p>
  <p><strong>4. Basketball & Hockey:</strong> These sports showed the <strong>worst results</strong> for Over bettors. If you see a high-EV Under in the NBA, that is the gold standard of this strategy.</p>
</div>
""", unsafe_allow_html=True)

# Hunt button
if st.button("🦄  HUNT FOR UNICORNS"):
    with st.spinner("Scanning markets…"):
        do_fetch()
    st.rerun()

# Updated text
if ts:
    secs   = int(time.time() - ts)
    nxt    = max(0, CACHE_SECS - secs)
    if secs < 10:
        upd = "Just refreshed"
    elif secs < 60:
        upd = f"Refreshed {secs}s ago · next in {nxt}s"
    else:
        upd = f"Refreshed {secs//60}m ago · next in {nxt//60}m {nxt%60}s"
    st.markdown(f"<div class='pv-updated'>{upd}</div>", unsafe_allow_html=True)

# Errors
for e in errs:
    st.markdown(f"<div class='pv-err'>⚠️ {e}</div>", unsafe_allow_html=True)

# Bet cards
if not bets:
    st.markdown("<div class='pv-empty'>No edges found right now — markets are tight.<br>Check back soon.</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='section-lbl'>Live Edges</div>", unsafe_allow_html=True)
    for bet in bets:
        ev       = bet["EV %"]
        sport    = bet["Sport"]
        tier_cls = "is-unicorn" if ev >= 7 else "is-premium" if ev >= 5 else ""
        tier_lbl = "🦄 Unicorn" if ev >= 7 else "⚡ Premium" if ev >= 5 else "📊 Standard"
        ev_col   = "#7dd3fc" if ev >= 7 else "#fbbf24" if ev >= 5 else "#94a3b8"
        tier_col = "#7dd3fc" if ev >= 7 else "#f59e0b" if ev >= 5 else "#475569"
        sp_cls   = "mlb" if sport == "MLB" else "nba"
        sp_ico   = "⚾" if sport == "MLB" else "🏀"
        od_cls   = "pos" if bet["Target Odds"].startswith("+") else "neg"

        st.markdown(f"""
        <div class="bet-card {tier_cls}">
          <div class="sport-bubble {sp_cls}">{sp_ico}</div>
          <div class="bet-body">
            <div class="bet-tier-lbl" style="color:{tier_col};">{tier_lbl}</div>
            <div class="bet-side">{bet["Side"]}</div>
            <div class="bet-meta">{bet["Game"]} · {bet["Market"]} · {sport}</div>
            <div class="bet-odds-row">
              <span class="odds-tag {od_cls}">{bet["Target Odds"]}</span>
              <span class="odds-vs">vs fair</span>
              <span class="odds-fair">{bet["Fair Odds"]}</span>
            </div>
          </div>
          <div class="bet-right">
            <div class="ev-pct" style="color:{ev_col};">+{ev}%</div>
            <div class="ev-lbl">Expected Value</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="pv-footer">
  Sharp: Pinnacle &nbsp;·&nbsp; Devig: Additive &nbsp;·&nbsp; Book: Novig &nbsp;·&nbsp; Min EV: 2.0%
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

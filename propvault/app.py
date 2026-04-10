"""
PropVault — +EV Engine
Railway deployment. Run: streamlit run app.py
"""

import os
import time
import requests
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

/* ── Live scores ticker ── */
.scores-bar {
  background: #060810;
  border-bottom: 1px solid #0f1628;
  padding: 9px 0;
  overflow: hidden;
  white-space: nowrap;
}
.scores-track {
  display: inline-flex;
  animation: scroll-left 50s linear infinite;
}
.scores-track:hover { animation-play-state: paused; }
@keyframes scroll-left { 0% { transform:translateX(0); } 100% { transform:translateX(-50%); } }
.score-chip {
  display: inline-flex; align-items: center; gap: 7px;
  margin: 0 24px;
  font-size: 12px; font-weight: 700; color: #2a4060;
  letter-spacing: 0.3px;
}
.score-chip .sc-sport {
  font-size: 9px; font-weight: 800; letter-spacing: 2px;
  text-transform: uppercase; padding: 2px 6px;
  border-radius: 5px;
}
.score-chip .sc-sport.mlb { background:#0a1a2e; color:#2a5a8a; }
.score-chip .sc-sport.nba { background:#1a0808; color:#8a2a2a; }
.score-chip .sc-teams { color:#3a5878; }
.score-chip .sc-score { color:#7dd3fc; font-weight:900; }
.score-chip .sc-status { color:#1e3050; }
.score-chip .sc-sep { color:#0f1628; font-size:18px; }

/* ── EV ticker ── */
.ev-ticker-bar {
  background: #0d1222;
  border-bottom: 1px solid #141e30;
  padding: 10px 0;
  overflow: hidden;
  white-space: nowrap;
}
.ev-ticker-track {
  display: inline-flex;
  animation: scroll-left 35s linear infinite;
}
.ev-ticker-track:hover { animation-play-state: paused; }
.ev-chip {
  display: inline-flex; align-items: center; gap: 8px;
  margin: 0 20px;
  font-size: 12px; font-weight: 600; color: #2a4060;
}
.ev-chip .t-game { color:#3a5878; }
.ev-chip .t-ev   { color:#22c55e; font-weight:900; }
.ev-chip .t-sep  { color:#0f1628; font-size:18px; }

/* ── Page shell ── */
.pv-page { max-width: 860px; margin: 0 auto; padding: 28px 24px 60px; }

/* ── Header ── */
.pv-header {
  display: flex; align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  gap: 16px;
}
.pv-logo { display: flex; align-items: center; gap: 16px; }
.pv-logo-name {
  font-size: 42px; font-weight: 900;
  background: linear-gradient(90deg, #7dd3fc 0%, #ffffff 60%, #e0f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1.5px; line-height: 1;
}
.pv-logo-sub {
  font-size: 12px; font-weight: 600;
  color: #1e3050; letter-spacing: 0.5px; margin-top: 3px;
}
.pv-header-right {
  display: flex; align-items: center; gap: 12px; flex-shrink: 0;
}
.pv-beer-btn {
  display: flex; align-items: center; gap: 7px;
  background: #0d1525; border: 1.5px solid #1e3050;
  border-radius: 100px; padding: 9px 18px;
  font-size: 14px; font-weight: 700; color: #4a7090;
  text-decoration: none; letter-spacing: 0.3px;
  transition: all 0.2s;
}
.pv-beer-btn:hover { border-color: #7dd3fc; color: #7dd3fc; }
.pv-live {
  display: flex; align-items: center; gap: 8px;
  background: #0a1e10; border: 1.5px solid #166534;
  border-radius: 100px; padding: 9px 20px;
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
  background: #0d1525; border-radius: 22px;
  padding: 22px 24px; border: 1.5px solid #141e30;
}
.pv-stat-num {
  font-size: 40px; font-weight: 900;
  letter-spacing: -2px; line-height: 1; margin-bottom: 5px;
}
.pv-stat-lbl {
  font-size: 11px; font-weight: 700;
  letter-spacing: 1.5px; text-transform: uppercase; color: #1e3050;
}

/* ── Card ── */
.card {
  background: #0d1525; border-radius: 22px;
  border: 1.5px solid #141e30; padding: 26px 28px; margin-bottom: 14px;
}

/* ── Guide ── */
.guide-title { font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 8px; }
.guide-sub   { font-size: 14px; color: #4a6a8a; line-height: 1.6; margin-bottom: 22px; }
.tiers { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 18px; }
.tier {
  background: #080c18; border-radius: 16px;
  padding: 18px 16px; text-align: center; border: 1.5px solid #141e30;
}
.tier-top { height: 4px; border-radius: 2px; margin-bottom: 12px; }
.tier-name { font-size: 10px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; }
.tier-range { font-size: 20px; font-weight: 800; color: #fff; }
.logic-box {
  background: #080c18; border-radius: 14px; padding: 16px 18px;
  border: 1.5px solid #141e30; font-size: 13px; line-height: 1.65; color: #4a6a8a;
}
.logic-box strong { color: #7dd3fc; font-weight: 800; }

/* ── Strategy ── */
.strategy-title {
  font-size: 16px; font-weight: 800; color: #ef4444;
  letter-spacing: 0.5px; text-transform: uppercase;
  margin-bottom: 16px;
}
.strategy p { font-size: 14px; color: #8aaac8; line-height: 1.7; margin-bottom: 10px; }
.strategy p:last-child { margin-bottom: 0; }
.strategy strong { color: #e2e8f0; }
.s-stat {
  display: inline-block; border-radius: 8px;
  padding: 2px 8px; font-size: 13px; font-weight: 800;
}

/* ── Hunt button ── */
div.stButton { display: flex; justify-content: center; margin: 8px 0 6px; }
div.stButton > button {
  width: 380px !important; height: 64px !important;
  background: #0d1525 !important; border: 2px solid #7dd3fc !important;
  border-radius: 18px !important; color: #7dd3fc !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 900 !important; font-size: 17px !important;
  letter-spacing: 2px !important; text-transform: uppercase !important;
  transition: all 0.2s !important;
}
div.stButton > button:hover {
  background: #111d35 !important;
  box-shadow: 0 0 28px rgba(125,211,252,0.12) !important;
}

/* ── Updated ── */
.pv-updated {
  text-align: center; font-size: 12px; color: #1e3050;
  font-weight: 600; letter-spacing: 0.5px; margin: 10px 0 20px;
}

/* ── Section label ── */
.section-lbl {
  font-size: 11px; font-weight: 800; color: #1e3050;
  letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14px;
}

/* ── Bet card ── */
.bet-card {
  background: #0d1525; border-radius: 22px;
  border: 1.5px solid #141e30; padding: 22px 24px;
  margin-bottom: 12px; display: flex; align-items: center; gap: 20px;
}
.bet-card.is-unicorn { border-color: #1a3a5a; background: #0a1828; }
.bet-card.is-premium { border-color: #2a2010; }

.sport-bubble {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; flex-shrink: 0; border: 1.5px solid;
}
.sport-bubble.mlb { background:#081428; border-color:#0e2040; }
.sport-bubble.nba { background:#180808; border-color:#280e0e; }

.bet-body { flex: 1; min-width: 0; }
.bet-tier-lbl {
  font-size: 10px; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;
}
.bet-side {
  font-size: 22px; font-weight: 800; color: #f8fafc;
  margin-bottom: 4px; letter-spacing: -0.3px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bet-meta { font-size: 13px; color: #2a4060; font-weight: 600; margin-bottom: 12px; }
.bet-odds-row { display: flex; align-items: center; gap: 10px; }
.odds-tag {
  font-size: 16px; font-weight: 800;
  padding: 5px 14px; border-radius: 12px;
}
.odds-tag.pos { color:#4ade80; background:#051410; border:1.5px solid #0a2818; }
.odds-tag.neg { color:#93c5fd; background:#050e1c; border:1.5px solid #0a1828; }
.odds-vs   { font-size: 11px; color: #1a2e44; font-weight: 700; }
.odds-fair { font-size: 14px; color: #2a4a6a; font-weight: 700; }

.bet-right { text-align: right; flex-shrink: 0; min-width: 110px; }
.ev-pct {
  font-size: 38px; font-weight: 900;
  letter-spacing: -2px; line-height: 1;
}
.ev-lbl {
  font-size: 10px; font-weight: 700; color: #1a3050;
  text-transform: uppercase; letter-spacing: 1.5px; margin-top: 3px;
}

/* ── Empty / error ── */
.pv-empty {
  text-align: center; padding: 70px 0;
  font-size: 16px; font-weight: 700; color: #1a2a3a;
}
.pv-err {
  background: #160808; border: 1.5px solid #3a0a0a;
  border-radius: 14px; padding: 12px 18px;
  font-size: 13px; color: #fca5a5; margin-bottom: 10px; font-weight: 600;
}

/* ── Footer ── */
.pv-footer {
  text-align: center; font-size: 11px; color: #0d1828;
  letter-spacing: 2px; text-transform: uppercase; margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# ── Custom unicorn SVG ────────────────────────────────────────────────────────
UNICORN_SVG = """
<svg width="54" height="54" viewBox="0 0 54 54" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#7dd3fc" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#7dd3fc" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="body" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#c084fc"/>
      <stop offset="50%" stop-color="#7dd3fc"/>
      <stop offset="100%" stop-color="#a78bfa"/>
    </linearGradient>
    <linearGradient id="horn" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fde68a"/>
      <stop offset="100%" stop-color="#f59e0b"/>
    </linearGradient>
    <filter id="blur-glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <!-- Outer glow -->
  <circle cx="27" cy="27" r="26" fill="url(#glow)"/>
  <!-- Body -->
  <ellipse cx="27" cy="32" rx="14" ry="11" fill="url(#body)" opacity="0.95" filter="url(#blur-glow)"/>
  <!-- Head -->
  <circle cx="27" cy="20" r="10" fill="url(#body)" opacity="0.95"/>
  <!-- Horn -->
  <polygon points="27,4 24,16 30,16" fill="url(#horn)" opacity="0.95"/>
  <!-- Horn shine -->
  <line x1="27" y1="6" x2="25.5" y2="14" stroke="#fef9c3" stroke-width="1" stroke-linecap="round" opacity="0.7"/>
  <!-- Eye -->
  <circle cx="30" cy="19" r="2" fill="#0a0e1a"/>
  <circle cx="30.7" cy="18.3" r="0.7" fill="#fff" opacity="0.8"/>
  <!-- Mane -->
  <path d="M20 16 Q16 20 18 26 Q15 22 17 28" stroke="#f0abfc" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.9"/>
  <path d="M19 14 Q14 18 16 25" stroke="#7dd3fc" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.8"/>
  <!-- Legs -->
  <rect x="19" y="40" width="4" height="9" rx="2" fill="url(#body)" opacity="0.8"/>
  <rect x="25" y="41" width="4" height="8" rx="2" fill="url(#body)" opacity="0.8"/>
  <rect x="31" y="40" width="4" height="9" rx="2" fill="url(#body)" opacity="0.8"/>
  <!-- Tail -->
  <path d="M41 32 Q48 28 46 38 Q44 44 40 42" stroke="#c084fc" stroke-width="3" stroke-linecap="round" fill="none" opacity="0.9"/>
  <path d="M41 32 Q50 25 47 36" stroke="#7dd3fc" stroke-width="1.5" stroke-linecap="round" fill="none" opacity="0.7"/>
  <!-- Star sparkles -->
  <circle cx="8" cy="10" r="1.5" fill="#fde68a" opacity="0.9"/>
  <circle cx="46" cy="8" r="1" fill="#7dd3fc" opacity="0.8"/>
  <circle cx="6" cy="38" r="1" fill="#c084fc" opacity="0.7"/>
  <circle cx="48" cy="44" r="1.5" fill="#fde68a" opacity="0.6"/>
</svg>
"""

# ── Live scores fetch ─────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def fetch_live_scores():
    scores = []
    try:
        for league, label in [("mlb", "MLB"), ("nba", "NBA")]:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/{'baseball' if league=='mlb' else 'basketball'}/{league}/scoreboard",
                timeout=5
            )
            if r.status_code != 200:
                continue
            for event in r.json().get("events", []):
                comp = event["competitions"][0]
                teams = comp["competitors"]
                home = next((t for t in teams if t["homeAway"] == "home"), teams[0])
                away = next((t for t in teams if t["homeAway"] == "away"), teams[1])
                status = event["status"]["type"]["shortDetail"]
                scores.append({
                    "sport":  label,
                    "away":   away["team"]["abbreviation"],
                    "home":   home["team"]["abbreviation"],
                    "a_score": away.get("score", ""),
                    "h_score": home.get("score", ""),
                    "status": status,
                })
    except Exception:
        pass
    return scores

# ── EV bets fetch ─────────────────────────────────────────────────────────────
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

bets = st.session_state.bets
errs = st.session_state.errors
ts   = st.session_state.fetched_at

# ── Live scores ticker ────────────────────────────────────────────────────────
live_scores = fetch_live_scores()
if live_scores:
    chips = ""
    for s in live_scores:
        sc = f"{s['away']} {s['a_score']} · {s['home']} {s['h_score']}" if s["a_score"] != "" else f"{s['away']} vs {s['home']}"
        chips += f"""<span class="score-chip">
          <span class="sc-sport {s['sport'].lower()}">{s['sport']}</span>
          <span class="sc-teams">{sc}</span>
          <span class="sc-score"></span>
          <span class="sc-status">{s['status']}</span>
        </span><span class="score-chip"><span class="sc-sep">·</span></span>"""
    st.markdown(f'<div class="scores-bar"><div class="scores-track">{chips}{chips}</div></div>', unsafe_allow_html=True)

# ── EV ticker ─────────────────────────────────────────────────────────────────
if bets:
    ev_items = ""
    for b in bets:
        ico = "🦄" if b["EV %"] >= 7 else "⚡" if b["EV %"] >= 5 else "📊"
        ev_items += f'<span class="ev-chip">{ico} <span class="t-game">{b["Side"]} — {b["Game"]}</span><span class="t-ev">+{b["EV %"]}%</span></span><span class="ev-chip"><span class="t-sep">·</span></span>'
    st.markdown(f'<div class="ev-ticker-bar"><div class="ev-ticker-track">{ev_items}{ev_items}</div></div>', unsafe_allow_html=True)

# ── Page ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="pv-page">', unsafe_allow_html=True)

# Header
avg_ev = round(sum(b["EV %"] for b in bets) / len(bets), 1) if bets else 0.0
top_ev = bets[0]["EV %"] if bets else 0.0

st.markdown(f"""
<div class="pv-header">
  <div class="pv-logo">
    {UNICORN_SVG}
    <div>
      <div class="pv-logo-name">PropVault</div>
      <div class="pv-logo-sub">Novig vs Pinnacle · Sharp Edge Finder</div>
    </div>
  </div>
  <div class="pv-header-right">
    <a class="pv-beer-btn" href="https://www.buymeacoffee.com/notjxck" target="_blank">🍺 Buy me a beer</a>
    <div class="pv-live"><div class="pv-live-dot"></div>LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Stats
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
    <div class="pv-stat-num" style="color:#fbbf24">+{top_ev}%</div>
    <div class="pv-stat-lbl">Top EV</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Guide
st.markdown("""
<div class="card">
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
<div class="card strategy" style="border-left: 3px solid #ef4444;">
  <div class="strategy-title">📉 The "Anti-Public" Strategy</div>
  <p><strong>1. The "Fun" Tax:</strong> A community study of <span class="s-stat" style="background:#0a1e10;color:#4ade80;">4,344 bets</span> found Over props returned <span class="s-stat" style="background:#1a0808;color:#f87171;">-2.26% ROI</span> while Under props returned <span class="s-stat" style="background:#0a1e10;color:#4ade80;">+3.33% ROI</span> with a 56% win rate. Books bake in juice because the public wants to cheer for points.</p>
  <p><strong>2. One Path vs. Ten:</strong> To hit an Over, everything must go perfectly. An <strong>Under</strong> wins if there is an injury, blowout, foul trouble, or just a bad night.</p>
  <p><strong>3. Pitcher Strikeout Unders:</strong> A pitcher hits an Under if they get shelled or hit a pitch count. An Over requires flawless play for 6+ innings. <em>Bet on the chaos, not the perfection.</em></p>
  <p><strong>4. Basketball & Hockey:</strong> These sports showed the <strong>worst results</strong> for Over bettors. A high-EV Under in the NBA is the gold standard of this strategy.</p>
</div>
""", unsafe_allow_html=True)

# Hunt button
if st.button("🦄  HUNT FOR UNICORNS"):
    with st.spinner("Scanning markets…"):
        do_fetch()
    st.rerun()

# Updated text
if ts:
    secs = int(time.time() - ts)
    nxt  = max(0, CACHE_SECS - secs)
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

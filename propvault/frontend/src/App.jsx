import { useState, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const REFRESH_INTERVAL_MS = 60_000; // re-poll every 60 seconds

function americanToDecimal(o) { return o > 0 ? o / 100 + 1 : 100 / Math.abs(o) + 1; }
function fmtOdds(o) { return o > 0 ? `+${o}` : `${o}`; }

function SportIcon({ sport }) {
  const mlb = sport === "MLB";
  return (
    <div style={{
      width: 44, height: 44, borderRadius: "50%",
      background: mlb ? "#1e3a5f" : "#3b1f1f",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: 20, flexShrink: 0,
    }}>
      {mlb ? "⚾" : "🏀"}
    </div>
  );
}

function Spinner() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "60px 0", gap: 16 }}>
      <div style={{
        width: 36, height: 36, borderRadius: "50%",
        border: "3px solid #1e2a38",
        borderTopColor: "#22c55e",
        animation: "spin 0.7s linear infinite",
      }} />
      <span style={{ fontSize: 13, color: "#64748b" }}>Scanning for +EV bets…</span>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div style={{ textAlign: "center", padding: "60px 20px" }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
      <div style={{ fontSize: 14, color: "#f87171", marginBottom: 8, fontWeight: 600 }}>Something went wrong</div>
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 20 }}>{message}</div>
      <button
        onClick={onRetry}
        style={{
          background: "#22c55e22", border: "1px solid #22c55e44",
          color: "#22c55e", borderRadius: 8, padding: "8px 20px",
          fontSize: 13, fontWeight: 600, cursor: "pointer",
        }}
      >
        Try Again
      </button>
    </div>
  );
}

export default function EVFinder() {
  const [bets, setBets] = useState([]);
  const [stats, setStats] = useState({ count: 0, avg_ev: 0, top_ev: 0 });
  const [status, setStatus] = useState("loading"); // loading | success | error
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchBets = useCallback(async () => {
    setStatus("loading");
    setError("");
    try {
      const res = await fetch(`${API_BASE}/ev-bets`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Server error ${res.status}`);
      }
      const data = await res.json();
      setBets(data.bets ?? []);
      setStats({
        count: data.count ?? 0,
        avg_ev: data.avg_ev ?? 0,
        top_ev: data.top_ev ?? 0,
      });
      setLastUpdated(new Date());
      setStatus("success");
    } catch (err) {
      setError(err.message ?? "Unknown error");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    fetchBets();
    const interval = setInterval(fetchBets, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchBets]);

  const avgEV = stats.avg_ev.toFixed(1);
  const topEV = stats.top_ev.toFixed(1);
  const timeStr = lastUpdated
    ? lastUpdated.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0d1117",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      color: "#e2e8f0",
      maxWidth: 520,
      margin: "0 auto",
      padding: "0 0 40px",
    }}>

      {/* ── Header ── */}
      <div style={{ padding: "24px 20px 16px", borderBottom: "1px solid #1e2533" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: "linear-gradient(135deg, #22c55e, #16a34a)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 16,
            }}>💰</div>
            <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: -0.3, color: "#fff" }}>PropVault</span>
          </div>
          <div style={{
            background: status === "loading" ? "#22c55e11" : "#22c55e22",
            border: `1px solid ${status === "loading" ? "#22c55e22" : "#22c55e44"}`,
            borderRadius: 20, padding: "4px 12px",
            fontSize: 11, fontWeight: 600,
            color: status === "loading" ? "#22c55e88" : "#22c55e",
            letterSpacing: 0.5,
            display: "flex", alignItems: "center", gap: 6,
          }}>
            {status === "loading" && (
              <span style={{
                width: 6, height: 6, borderRadius: "50%",
                background: "#22c55e88",
                display: "inline-block",
                animation: "pulse 1s ease-in-out infinite",
              }} />
            )}
            {status === "loading" ? "UPDATING" : "LIVE"}
            <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.3 } }`}</style>
          </div>
        </div>
        <p style={{ fontSize: 13, color: "#8899aa", margin: "8px 0 0" }}>
          +EV bets on Novig, sharp-priced against Pinnacle
        </p>
        {timeStr && (
          <p style={{ fontSize: 11, color: "#3a5060", margin: "4px 0 0" }}>
            Last updated {timeStr} · refreshes every 60s
          </p>
        )}
      </div>

      {/* ── Summary row ── */}
      <div style={{
        display: "flex", padding: "14px 20px",
        borderBottom: "1px solid #1e2533",
        background: "#0a0e14",
      }}>
        {[
          { label: "Bets Found", value: stats.count, green: true },
          { label: "Avg EV", value: `+${avgEV}%`, green: false },
          { label: "Top EV", value: stats.count ? `+${topEV}%` : "—", green: true },
        ].map((s, i) => (
          <div key={i} style={{
            flex: 1, textAlign: "center",
            borderRight: i < 2 ? "1px solid #1e2533" : "none",
          }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: s.green ? "#22c55e" : "#e2e8f0" }}>{s.value}</div>
            <div style={{ fontSize: 10, color: "#7a8fa8", marginTop: 2, letterSpacing: 0.5, textTransform: "uppercase" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Content ── */}
      <div style={{ padding: "12px 16px 0" }}>
        {status === "loading" && bets.length === 0 && <Spinner />}
        {status === "error" && <ErrorState message={error} onRetry={fetchBets} />}
        {(status === "success" || (status === "loading" && bets.length > 0)) && bets.length === 0 && (
          <div style={{ textAlign: "center", padding: "60px 0", color: "#64748b", fontSize: 13 }}>
            No +EV bets found right now. Check back soon.
          </div>
        )}
        {bets.map((bet, i) => {
          const evColor = bet.ev >= 8 ? "#4ade80" : bet.ev >= 5 ? "#facc15" : bet.ev >= 3 ? "#fb923c" : "#94a3b8";
          return (
            <div key={bet.id} style={{
              background: "#131920",
              borderRadius: 14,
              padding: "16px 16px",
              marginBottom: 10,
              display: "flex",
              alignItems: "center",
              gap: 14,
              border: "1px solid #1e2a38",
              opacity: status === "loading" ? 0.6 : 1,
              transition: "opacity 0.2s",
            }}>
              <SportIcon sport={bet.sport} />

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#f1f5f9", marginBottom: 3, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {bet.side}
                </div>
                <div style={{ fontSize: 12, color: "#7a8fa8", marginBottom: 6 }}>
                  {bet.game} · {bet.market} · {bet.sport}
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: bet.novig_odds > 0 ? "#4ade80" : "#cbd5e1" }}>
                    {fmtOdds(bet.novig_odds)}
                  </span>
                  <span style={{ fontSize: 11, color: "#64748b" }}>vs fair</span>
                  <span style={{ fontSize: 12, color: "#8899aa" }}>{bet.fair_odds}</span>
                </div>
              </div>

              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: evColor, letterSpacing: -0.5 }}>
                  +{bet.ev.toFixed(1)}%
                </div>
                <div style={{ fontSize: 10, color: "#64748b", marginTop: 2, textTransform: "uppercase", letterSpacing: 0.5 }}>EV</div>
                <div style={{
                  marginTop: 6, fontSize: 9, fontWeight: 600,
                  color: "#4a9060", background: "#0f2018",
                  borderRadius: 4, padding: "2px 6px",
                  letterSpacing: 0.5, textTransform: "uppercase",
                }}>
                  #{i + 1}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Footer ── */}
      <div style={{ textAlign: "center", padding: "20px 20px 0", fontSize: 11, color: "#4a6070", letterSpacing: 0.5 }}>
        SHARP: PINNACLE · DEVIG: ADDITIVE · BOOK: NOVIG
      </div>
    </div>
  );
}

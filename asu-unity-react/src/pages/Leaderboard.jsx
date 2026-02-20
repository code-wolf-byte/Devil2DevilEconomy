import { useState, useEffect, useMemo } from "react";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-theme.bundle.css";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-header-footer.css";
import { Hero } from "@asu/unity-react-core";
import heroImage from "../assets/Hero.jpg";

// Rank metadata indexed by 0-based rank position
const RANK_META = [
  {
    label: "1st Place",
    icon: "🏆",
    avatarSize: 96,
    elevated: true,
    badgeBg: "#FFC627",
    badgeColor: "#1a1a1a",
    accentBorder: "3px solid #FFC627",
  },
  {
    label: "2nd Place",
    icon: "🥈",
    avatarSize: 76,
    elevated: false,
    badgeBg: "#9e9e9e",
    badgeColor: "#fff",
    accentBorder: "3px solid #9e9e9e",
  },
  {
    label: "3rd Place",
    icon: "🥉",
    avatarSize: 76,
    elevated: false,
    badgeBg: "#cd7f32",
    badgeColor: "#fff",
    accentBorder: "3px solid #cd7f32",
  },
];

function Avatar({ src, alt, size }) {
  const [errored, setErrored] = useState(false);
  const initials = (alt || "?").slice(0, 2).toUpperCase();

  if (!src || errored) {
    return (
      <div
        className="rounded-circle d-inline-flex align-items-center justify-content-center fw-bold text-white"
        style={{
          width: size,
          height: size,
          background: "#8C1D40",
          fontSize: size * 0.35,
          border: "3px solid #fff",
          boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
          flexShrink: 0,
        }}
      >
        {initials}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      onError={() => setErrored(true)}
      className="rounded-circle"
      style={{
        width: size,
        height: size,
        objectFit: "cover",
        border: "3px solid #fff",
        boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
        flexShrink: 0,
      }}
    />
  );
}

export default function Leaderboard() {
  const [status, setStatus] = useState({ loading: true, error: null });
  const [users, setUsers] = useState([]);
  const [totals, setTotals] = useState(null);

  const apiBaseUrl = useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      try {
        const url = apiBaseUrl ? `${apiBaseUrl}/api/leaderboard` : "/api/leaderboard";
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        const data = await res.json();
        if (isMounted) {
          setUsers(Array.isArray(data.users) ? data.users : []);
          setTotals(data.totals || null);
          setStatus({ loading: false, error: null });
        }
      } catch (err) {
        if (isMounted) setStatus({ loading: false, error: err.message });
      }
    };
    load();
    return () => { isMounted = false; };
  }, [apiBaseUrl]);

  const topThree = users.slice(0, 3);
  const rest = users.slice(3);

  // Classic podium display order: 2nd (left) · 1st (centre) · 3rd (right)
  const podiumSlots = [
    topThree[1] ? { user: topThree[1], rankIdx: 1 } : null,
    topThree[0] ? { user: topThree[0], rankIdx: 0 } : null,
    topThree[2] ? { user: topThree[2], rankIdx: 2 } : null,
  ].filter(Boolean);

  if (status.loading) {
    return (
      <div className="container-xl py-5">
        <p className="text-muted">Loading rankings…</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container-xl py-5">
        <p className="text-danger">Failed to load leaderboard: {status.error}</p>
      </div>
    );
  }

  return (
    <main id="main-content">

      {/* ── Hero ── */}
      <Hero
        type="heading-hero"
        image={{ url: heroImage, altText: "Sun Devil Rankings", size: "medium" }}
        title={{ text: "Sun Devil Rankings", highlightColor: "gold" }}
        contents={[{ text: "Who's earning the most pitchforks in the Devil2Devil community?" }]}
        contentsColor="white"
      />

      {/* ── Community stats bar ── */}
      {totals && (
        <div className="gray-dark-bg">
          <div className="container-xl">
            <div className="row g-0 text-center">
              <div className="col-12 col-md-4 py-4" style={{ borderRight: "1px solid rgba(255,255,255,0.15)" }}>
                <div
                  className="fw-bold mb-1"
                  style={{ color: "#FFC627", fontSize: "1.75rem", lineHeight: 1 }}
                >
                  {totals.total_users.toLocaleString()}
                </div>
                <div className="small text-white" style={{ opacity: 0.7 }}>Sun Devils</div>
              </div>
              <div className="col-12 col-md-4 py-4" style={{ borderRight: "1px solid rgba(255,255,255,0.15)" }}>
                <div
                  className="fw-bold mb-1 d-inline-flex align-items-center gap-2"
                  style={{ color: "#FFC627", fontSize: "1.75rem", lineHeight: 1 }}
                >
                  <img src="/static/Coin_Gold.png" alt="" style={{ width: 22, height: 22 }} />
                  {totals.total_balance.toLocaleString()}
                </div>
                <div className="small text-white" style={{ opacity: 0.7 }}>Pitchforks in Circulation</div>
              </div>
              <div className="col-12 col-md-4 py-4">
                <div
                  className="fw-bold mb-1"
                  style={{ color: "#FFC627", fontSize: "1.75rem", lineHeight: 1 }}
                >
                  {totals.total_points.toLocaleString()}
                </div>
                <div className="small text-white" style={{ opacity: 0.7 }}>Total Points Earned</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Podium (top 3) ── */}
      {topThree.length > 0 && (
        <section className="py-5 bg topo-white">
          <div className="container-xl">
            <div className="text-center mb-5">
              <h2 className="h3 fw-bold mb-1">
                <span className="highlight-gold">Top Sun Devils</span>
              </h2>
              <p className="text-muted mb-0">The highest pitchfork earners in Devil2Devil</p>
            </div>

            <div className="row g-4 justify-content-center align-items-end">
              {podiumSlots.map(({ user, rankIdx }) => {
                const meta = RANK_META[rankIdx];
                return (
                  <div
                    key={user.id}
                    className="col-12 col-md-4"
                    style={meta.elevated ? { transform: "translateY(-20px)" } : {}}
                  >
                    <div
                      className="rounded overflow-hidden text-center"
                      style={{
                        boxShadow: meta.elevated
                          ? "0 12px 40px rgba(140,29,64,0.25)"
                          : "0 4px 16px rgba(0,0,0,0.1)",
                        border: meta.accentBorder,
                      }}
                    >
                      {/* Maroon header band */}
                      <div
                        className="py-4 px-3"
                        style={{ background: "#8C1D40" }}
                      >
                        <div
                          className="d-inline-flex align-items-center gap-2 rounded-pill px-3 py-1 mb-3 fw-semibold small"
                          style={{ background: meta.badgeBg, color: meta.badgeColor }}
                        >
                          {meta.icon} {meta.label}
                        </div>
                        <div>
                          <Avatar
                            src={user.avatar_url}
                            alt={user.username}
                            size={meta.avatarSize}
                          />
                        </div>
                      </div>

                      {/* Card body */}
                      <div className="bg-white p-4">
                        <h3 className="fw-bold mb-1" style={{ fontSize: meta.elevated ? "1.15rem" : "1rem" }}>
                          {user.username}
                        </h3>
                        <p className="text-muted small mb-3">
                          {user.points.toLocaleString()} pts earned
                        </p>
                        <div
                          className="d-inline-flex align-items-center gap-2 rounded-pill px-3 py-2"
                          style={{
                            background: "#FFF8E7",
                            border: "2px solid #FFC627",
                          }}
                        >
                          <img src="/static/Coin_Gold.png" alt="" style={{ width: 18, height: 18 }} />
                          <span
                            className="fw-bold"
                            style={{
                              color: "#8C1D40",
                              fontSize: meta.elevated ? "1.2rem" : "1rem",
                            }}
                          >
                            {user.balance.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* ── Rankings table (4th and beyond) ── */}
      {rest.length > 0 && (
        <section className="py-5 gray-faint-bg">
          <div className="container-xl">
            <h2 className="h4 fw-bold mb-4">
              <span className="highlight-gold">Full Rankings</span>
            </h2>
            <div className="rounded overflow-hidden shadow-sm" style={{ border: "1px solid #e3e3e3" }}>
              <table className="table table-hover align-middle mb-0 bg-white">
                <thead>
                  <tr style={{ background: "#8C1D40" }}>
                    <th className="ps-4 py-3 text-white fw-semibold" style={{ width: "80px" }}>Rank</th>
                    <th className="py-3 text-white fw-semibold">Sun Devil</th>
                    <th className="py-3 text-end text-white fw-semibold">Points Earned</th>
                    <th className="py-3 text-end pe-4 text-white fw-semibold">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {rest.map((user, index) => {
                    const rank = index + 4;
                    return (
                      <tr key={user.id}>
                        <td className="ps-4">
                          <span
                            className="fw-bold rounded-pill d-inline-flex align-items-center justify-content-center"
                            style={{
                              width: 32,
                              height: 32,
                              background: "#F5F5F5",
                              color: "#8C1D40",
                              fontSize: "0.85rem",
                            }}
                          >
                            #{rank}
                          </span>
                        </td>
                        <td>
                          <div className="d-flex align-items-center gap-3">
                            <Avatar src={user.avatar_url} alt={user.username} size={40} />
                            <span className="fw-semibold">{user.username}</span>
                          </div>
                        </td>
                        <td className="text-end text-muted">
                          {user.points.toLocaleString()}
                        </td>
                        <td className="text-end pe-4">
                          <span
                            className="d-inline-flex align-items-center gap-1 fw-bold"
                            style={{ color: "#8C1D40" }}
                          >
                            <img src="/static/Coin_Gold.png" alt="" style={{ width: 15, height: 15 }} />
                            {user.balance.toLocaleString()}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {users.length === 0 && (
        <section className="py-5 bg topo-white">
          <div className="container-xl text-center py-4">
            <p className="h5 text-muted">
              No Sun Devils on the board yet — start earning pitchforks!
            </p>
          </div>
        </section>
      )}

    </main>
  );
}

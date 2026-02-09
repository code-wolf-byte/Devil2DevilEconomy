import { useState, useEffect, useMemo } from "react";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-theme.bundle.css";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-header-footer.css";
import { Button } from "@asu/unity-react-core";

const rankStyles = [
  { bg: "bg-gold", badge: "bg-gold text-dark", icon: "fa-trophy", label: "1st" },
  { bg: "gray-light-bg", badge: "bg-secondary text-white", icon: "fa-medal", label: "2nd" },
  { bg: "gray-faint-bg", badge: "bg-dark text-white", icon: "fa-award", label: "3rd" },
];

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
    const loadLeaderboard = async () => {
      try {
        const url = apiBaseUrl ? `${apiBaseUrl}/api/leaderboard` : "/api/leaderboard";
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Leaderboard request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setUsers(Array.isArray(data.users) ? data.users : []);
          setTotals(data.totals || null);
          setStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) {
          setStatus({ loading: false, error: error.message });
        }
      }
    };

    loadLeaderboard();
    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl]);

  if (status.loading) {
    return (
      <div className="container-xl py-5">
        <h1 className="display-6 fw-bold mb-3">Leaderboard</h1>
        <p className="text-muted">Loading leaderboard...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container-xl py-5">
        <h1 className="display-6 fw-bold mb-3">Leaderboard</h1>
        <p className="text-danger">Failed to load leaderboard: {status.error}</p>
      </div>
    );
  }

  const topThree = users.slice(0, 3);
  const rest = users.slice(3);

  return (
    <main id="main-content">
      {/* Header */}
      <div className="bg-maroon py-5">
        <div className="container-xl text-center">
          <h1 className="display-5 fw-bold text-white mb-2">Leaderboard</h1>
          <p className="lead text-white mb-0" style={{ opacity: 0.8 }}>
            Top users by pitchfork balance
          </p>
        </div>
      </div>

      {/* Stats bar */}
      {totals && (
        <div className="gray-dark-bg">
          <div className="container-xl">
            <div className="row g-0 text-center">
              <div className="col-12 col-md-4 py-3 border-end border-secondary">
                <div className="text-gold fw-bold h4 mb-0">{totals.total_users}</div>
                <div className="text-white small" style={{ opacity: 0.75 }}>Total Users</div>
              </div>
              <div className="col-12 col-md-4 py-3 border-end border-secondary">
                <div className="text-gold fw-bold h4 mb-0 d-inline-flex align-items-center gap-2">
                  <img src="/static/Coin_Gold.png" alt="" style={{ width: 20, height: 20 }} />
                  {totals.total_balance}
                </div>
                <div className="text-white small" style={{ opacity: 0.75 }}>Total Balance</div>
              </div>
              <div className="col-12 col-md-4 py-3">
                <div className="text-gold fw-bold h4 mb-0">{totals.total_points}</div>
                <div className="text-white small" style={{ opacity: 0.75 }}>Points Earned</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top 3 podium */}
      {topThree.length > 0 && (
        <section className="py-5 bg topo-white">
          <div className="container-xl">
            <div className="row g-4 justify-content-center">
              {topThree.map((user, index) => {
                const style = rankStyles[index];
                return (
                  <div key={user.id} className="col-12 col-md-4">
                    <div className="border rounded bg-white text-center h-100 shadow-sm">
                      <div className={`${style.bg} py-4 rounded-top`}>
                        <span className={`badge ${style.badge} rounded-pill mb-2 px-3 py-2`}>
                          <i className={`fa-solid ${style.icon} me-1`} />
                          {style.label} Place
                        </span>
                        <div>
                          <img
                            src={user.avatar_url}
                            alt={user.username}
                            className="rounded-circle border border-3 border-white shadow-sm"
                            style={{ width: 80, height: 80, objectFit: "cover" }}
                          />
                        </div>
                      </div>
                      <div className="p-4">
                        <h3 className="h5 fw-bold mb-1">{user.username}</h3>
                        <p className="text-muted small mb-3">{user.points} total points earned</p>
                        <div className="d-inline-flex align-items-center gap-2 border rounded-pill px-3 py-2">
                          <img src="/static/Coin_Gold.png" alt="" style={{ width: 20, height: 20 }} />
                          <span className="fw-bold text-gold h5 mb-0">{user.balance}</span>
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

      {/* Remaining users */}
      {rest.length > 0 && (
        <section className="py-5 gray-faint-bg">
          <div className="container-xl">
            <h2 className="h4 fw-bold mb-4">
              <span className="highlight-gold">Other Rankings</span>
            </h2>
            <div className="border rounded bg-white shadow-sm">
              <div className="table-responsive">
                <table className="table table-hover align-middle mb-0">
                  <thead className="bg-maroon text-white">
                    <tr>
                      <th className="ps-4 py-3">Rank</th>
                      <th className="py-3">User</th>
                      <th className="py-3 text-end">Points Earned</th>
                      <th className="py-3 text-end pe-4">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rest.map((user, index) => (
                      <tr key={user.id}>
                        <td className="ps-4 fw-bold text-muted">#{index + 4}</td>
                        <td>
                          <div className="d-flex align-items-center gap-3">
                            <img
                              src={user.avatar_url}
                              alt={user.username}
                              className="rounded-circle"
                              style={{ width: 40, height: 40, objectFit: "cover" }}
                            />
                            <span className="fw-semibold">{user.username}</span>
                          </div>
                        </td>
                        <td className="text-end text-muted">{user.points}</td>
                        <td className="text-end pe-4">
                          <span className="fw-bold text-gold d-inline-flex align-items-center gap-1">
                            <img src="/static/Coin_Gold.png" alt="" style={{ width: 16, height: 16 }} />
                            {user.balance}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {users.length === 0 && (
        <div className="container-xl py-5 text-center">
          <p className="text-muted h5">No users yet. Be the first to join and start earning points!</p>
        </div>
      )}

      <div className="container-xl pb-5">
        <Button label="Back to Store" color="maroon" href="/store" />
      </div>
    </main>
  );
}

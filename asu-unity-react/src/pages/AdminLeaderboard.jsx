import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function AdminLeaderboard({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [data, setData] = React.useState(null);
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [currentPage, setCurrentPage] = React.useState(1);

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const loadData = React.useCallback(async (page = 1) => {
    try {
      setStatus({ loading: true, error: null });
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/admin/leaderboard?page=${page}`
        : `/api/admin/leaderboard?page=${page}`;
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        throw new Error(`Failed to load leaderboard (${response.status})`);
      }

      const result = await response.json();
      setData(result);
      setCurrentPage(page);
      setStatus({ loading: false, error: null });
    } catch (error) {
      setStatus({ loading: false, error: error.message });
    }
  }, [apiBaseUrl]);

  React.useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      return;
    }
    loadData(1);
  }, [isAuthenticated, isAdmin, loadData]);

  const handlePageChange = (page) => {
    loadData(page);
  };

  const formatDate = (isoString) => {
    if (!isoString) return "Unknown";
    const date = new Date(isoString);
    return date.toLocaleDateString();
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
        <Button label="Back to Dashboard" color="gray" href="/dashboard" />
      </div>
    );
  }

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <div className="text-center py-5">
          <div className="spinner-border text-warning mb-3" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted">Loading leaderboard data...</p>
        </div>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <div className="alert alert-danger">{status.error}</div>
        <Button label="Retry" color="gold" onClick={() => loadData(currentPage)} />
      </div>
    );
  }

  const { economy_stats, leaderboard_stats, top_spenders, most_active, pagination } = data || {};

  return (
    <div className="container py-5">
      <div className="text-center mb-4">
        <h1 className="display-6 fw-bold mb-2">Economy Leaderboard</h1>
        <p className="text-muted">View community statistics and top performers</p>
      </div>

      <div className="mb-4">
        <Button label="Back to Admin Panel" color="gray" href="/dashboard" />
      </div>

      <div className="border rounded bg-white p-4 mb-4">
        <h2 className="h5 fw-bold mb-3">Economy Overview</h2>
        <div className="row g-3">
          <div className="col-6 col-md-4 col-lg-2">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-warning mb-1">{economy_stats?.total_users || 0}</div>
              <div className="small text-muted">Total Users</div>
            </div>
          </div>
          <div className="col-6 col-md-4 col-lg-2">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-success mb-1">{economy_stats?.total_balance || 0}</div>
              <div className="small text-muted">Total Balance</div>
            </div>
          </div>
          <div className="col-6 col-md-4 col-lg-2">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-danger mb-1">{economy_stats?.total_spent || 0}</div>
              <div className="small text-muted">Total Spent</div>
            </div>
          </div>
          <div className="col-6 col-md-4 col-lg-2">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-primary mb-1">{economy_stats?.total_purchases || 0}</div>
              <div className="small text-muted">Total Purchases</div>
            </div>
          </div>
          <div className="col-6 col-md-4 col-lg-2">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-purple mb-1">{economy_stats?.total_achievements || 0}</div>
              <div className="small text-muted">Total Achievements</div>
            </div>
          </div>
          <div className="col-6 col-md-4 col-lg-2">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-info mb-1">{economy_stats?.average_balance || 0}</div>
              <div className="small text-muted">Average Balance</div>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-12 col-lg-4">
          <div className="border rounded bg-white p-4 h-100">
            <h3 className="h6 fw-bold mb-3 d-flex align-items-center gap-2">
              <img src="/static/Coin_Gold.png" alt="Balance" style={{ width: "20px", height: "20px" }} />
              Top Balances
            </h3>
            <div className="d-flex flex-column gap-2">
              {(leaderboard_stats || []).slice(0, 10).map((stat, index) => (
                <div key={stat.user.id} className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="fw-bold text-warning">{index + 1}</span>
                    <div>
                      <div className="fw-semibold">{stat.user.username}</div>
                      <div className="small text-muted">{stat.achievement_count} achievements</div>
                    </div>
                  </div>
                  <div className="text-end">
                    <div className="fw-bold text-warning">{stat.user.balance || 0}</div>
                    <div className="small text-muted">pitchforks</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-4">
          <div className="border rounded bg-white p-4 h-100">
            <h3 className="h6 fw-bold mb-3 d-flex align-items-center gap-2">
              <span className="text-danger">&#128722;</span>
              Top Spenders
            </h3>
            <div className="d-flex flex-column gap-2">
              {(top_spenders || []).map((stat, index) => (
                <div key={stat.user.id} className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="fw-bold text-danger">{index + 1}</span>
                    <div>
                      <div className="fw-semibold">{stat.user.username}</div>
                      <div className="small text-muted">{stat.purchase_count} purchases</div>
                    </div>
                  </div>
                  <div className="text-end">
                    <div className="fw-bold text-danger">{stat.total_spent}</div>
                    <div className="small text-muted">spent</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-4">
          <div className="border rounded bg-white p-4 h-100">
            <h3 className="h6 fw-bold mb-3 d-flex align-items-center gap-2">
              <span className="text-warning">&#128293;</span>
              Most Active
            </h3>
            <div className="d-flex flex-column gap-2">
              {(most_active || []).map((stat, index) => (
                <div key={stat.user.id} className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="fw-bold text-warning">{index + 1}</span>
                    <div>
                      <div className="fw-semibold">{stat.user.username}</div>
                      <div className="small text-muted">{stat.user.message_count || 0} messages</div>
                    </div>
                  </div>
                  <div className="text-end">
                    <div className="fw-bold text-warning">{stat.activity_score}</div>
                    <div className="small text-muted">activity</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="border rounded bg-white p-4">
        <h2 className="h5 fw-bold mb-3">Detailed Leaderboard</h2>

        <div className="d-none d-lg-block">
          <div className="table-responsive">
            <table className="table table-hover mb-0">
              <thead className="table-light">
                <tr>
                  <th className="text-warning">Rank</th>
                  <th className="text-warning">User</th>
                  <th className="text-warning">Balance</th>
                  <th className="text-warning">Spent</th>
                  <th className="text-warning">Purchases</th>
                  <th className="text-warning">Achievements</th>
                  <th className="text-warning">Messages</th>
                  <th className="text-warning">Voice Time</th>
                  <th className="text-warning">Activity</th>
                </tr>
              </thead>
              <tbody>
                {(leaderboard_stats || []).map((stat) => (
                  <tr key={stat.user.id}>
                    <td>
                      <div className="d-flex align-items-center gap-1">
                        {stat.rank <= 3 && <span className="text-warning">&#127942;</span>}
                        <span className="fw-bold">{stat.rank}</span>
                      </div>
                    </td>
                    <td>
                      <a
                        href={`/admin/users/${stat.user.id}`}
                        className="text-decoration-none text-dark fw-semibold"
                      >
                        {stat.user.username}
                      </a>
                      <div className="small text-muted">
                        {stat.user.is_admin && <span className="text-warning me-1">&#128081; Admin</span>}
                        {stat.user.has_boosted && <span className="text-purple me-1">&#11088; Booster</span>}
                        {stat.user.created_at && `Joined ${formatDate(stat.user.created_at)}`}
                      </div>
                    </td>
                    <td>
                      <span className="fw-bold text-warning d-flex align-items-center gap-1">
                        <img src="/static/Coin_Gold.png" alt="" style={{ width: "16px", height: "16px" }} />
                        {stat.user.balance || 0}
                      </span>
                    </td>
                    <td><span className="fw-bold text-danger">{stat.total_spent}</span></td>
                    <td><span className="fw-bold text-primary">{stat.purchase_count}</span></td>
                    <td><span className="fw-bold text-purple">{stat.achievement_count}</span></td>
                    <td><span className="fw-bold text-success">{stat.user.message_count || 0}</span></td>
                    <td><span className="fw-bold text-info">{stat.user.voice_minutes || 0}m</span></td>
                    <td><span className="fw-bold text-warning">{stat.activity_score}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="d-lg-none d-flex flex-column gap-3">
          {(leaderboard_stats || []).map((stat) => (
            <div key={stat.user.id} className="border rounded p-3 bg-light">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <div className="d-flex align-items-center gap-2">
                  <span className="h4 fw-bold text-warning mb-0">{stat.rank}</span>
                  <div>
                    <a
                      href={`/admin/users/${stat.user.id}`}
                      className="text-decoration-none text-dark fw-semibold"
                    >
                      {stat.user.username}
                    </a>
                    <div className="small text-muted">
                      {stat.user.is_admin && <span className="text-warning me-1">Admin</span>}
                      {stat.user.has_boosted && <span className="text-purple">Booster</span>}
                    </div>
                  </div>
                </div>
                <div className="text-end">
                  <div className="h5 fw-bold text-warning mb-0 d-flex align-items-center gap-1">
                    <img src="/static/Coin_Gold.png" alt="" style={{ width: "18px", height: "18px" }} />
                    {stat.user.balance || 0}
                  </div>
                  <div className="small text-muted">pitchforks</div>
                </div>
              </div>
              <div className="row g-2 small">
                <div className="col-6">
                  <div className="text-muted">Spent</div>
                  <div className="fw-bold text-danger">{stat.total_spent}</div>
                </div>
                <div className="col-6">
                  <div className="text-muted">Purchases</div>
                  <div className="fw-bold text-primary">{stat.purchase_count}</div>
                </div>
                <div className="col-6">
                  <div className="text-muted">Achievements</div>
                  <div className="fw-bold text-purple">{stat.achievement_count}</div>
                </div>
                <div className="col-6">
                  <div className="text-muted">Activity Score</div>
                  <div className="fw-bold text-warning">{stat.activity_score}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {pagination && pagination.pages > 1 && (
          <div className="d-flex flex-column flex-md-row align-items-center justify-content-between mt-4 gap-3">
            <div className="text-muted small">
              Showing {((pagination.page - 1) * pagination.per_page) + 1} -
              {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} users
            </div>
            <div className="d-flex align-items-center gap-2">
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                disabled={!pagination.has_prev}
                onClick={() => handlePageChange(pagination.prev_num)}
              >
                Previous
              </button>

              {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                let pageNum;
                if (pagination.pages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= pagination.pages - 2) {
                  pageNum = pagination.pages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    type="button"
                    className={`btn btn-sm ${pageNum === currentPage ? "btn-warning" : "btn-outline-secondary"}`}
                    onClick={() => handlePageChange(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                disabled={!pagination.has_next}
                onClick={() => handlePageChange(pagination.next_num)}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

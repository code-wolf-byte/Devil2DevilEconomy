import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function AdminUserDetail({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
  userId = null,
}) {
  const [data, setData] = React.useState(null);
  const [status, setStatus] = React.useState({ loading: true, error: null });

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const effectiveUserId = React.useMemo(() => {
    if (userId) return userId;
    const path = window.location.pathname;
    const match = path.match(/\/admin\/users\/([^/]+)/);
    return match ? match[1] : null;
  }, [userId]);

  const loadData = React.useCallback(async () => {
    if (!effectiveUserId) {
      setStatus({ loading: false, error: "User ID not provided" });
      return;
    }

    try {
      setStatus({ loading: true, error: null });
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/admin/users/${effectiveUserId}`
        : `/api/admin/users/${effectiveUserId}`;
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        throw new Error(`Failed to load user details (${response.status})`);
      }

      const result = await response.json();
      setData(result);
      setStatus({ loading: false, error: null });
    } catch (error) {
      setStatus({ loading: false, error: error.message });
    }
  }, [apiBaseUrl, effectiveUserId]);

  React.useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      return;
    }
    loadData();
  }, [isAuthenticated, isAdmin, loadData]);

  const formatDate = (isoString) => {
    if (!isoString) return "Unknown";
    const date = new Date(isoString);
    return date.toLocaleDateString();
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
        <Button label="Back to Dashboard" color="gray" href="/dashboard" />
      </div>
    );
  }

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <div className="text-center py-5">
          <div className="spinner-border text-warning mb-3" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted">Loading user data...</p>
        </div>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <div className="alert alert-danger">{status.error}</div>
        <Button label="Back to Leaderboard" color="gray" href="/admin-leaderboard" />
      </div>
    );
  }

  const { user, stats, earning_breakdown, spending_breakdown, achievements, recent_purchases, recent_achievements } = data || {};

  return (
    <div className="container py-5">
      <div className="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between mb-4 gap-3">
        <div className="d-flex align-items-center gap-3">
          <Button label="Back to Leaderboard" color="gray" href="/admin-leaderboard" />
          <h1 className="h3 fw-bold mb-0">{user?.username || "Unknown User"}</h1>
          {user?.is_admin && (
            <span className="badge bg-warning text-dark">&#128081; Admin</span>
          )}
          {user?.has_boosted && (
            <span className="badge bg-purple text-white">&#11088; Booster</span>
          )}
        </div>
        <div className="text-end">
          <div className="h4 fw-bold text-warning d-flex align-items-center gap-2">
            <img src="/static/Coin_Gold.png" alt="" style={{ width: "24px", height: "24px" }} />
            {user?.balance || 0}
          </div>
          <div className="small text-muted">Current Balance</div>
        </div>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-4 text-center">
            <div className="h3 fw-bold text-warning mb-1">{stats?.user_rank || "N/A"}</div>
            <div className="small text-muted">Global Rank</div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-4 text-center">
            <div className="h3 fw-bold text-success mb-1">{stats?.total_earned || 0}</div>
            <div className="small text-muted">Total Earned</div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-4 text-center">
            <div className="h3 fw-bold text-danger mb-1">{stats?.total_spent || 0}</div>
            <div className="small text-muted">Total Spent</div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-4 text-center">
            <div className="h3 fw-bold text-warning mb-1">{stats?.activity_score || 0}</div>
            <div className="small text-muted">Activity Score</div>
          </div>
        </div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-12 col-lg-6">
          <div className="border rounded bg-white p-4 h-100">
            <h2 className="h5 fw-bold mb-4 d-flex align-items-center gap-2">
              <span className="text-success">&#10133;</span>
              Points Earned Breakdown
            </h2>
            <div className="d-flex flex-column gap-2">
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-primary">&#128172;</span>
                  <span>Messages Sent</span>
                </div>
                <span className="fw-bold text-primary">{earning_breakdown?.messages || 0}</span>
              </div>
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-danger">&#10084;</span>
                  <span>Reactions Given</span>
                </div>
                <span className="fw-bold text-danger">{earning_breakdown?.reactions || 0}</span>
              </div>
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-purple">&#127908;</span>
                  <span>Voice Minutes</span>
                </div>
                <span className="fw-bold text-purple">{earning_breakdown?.voice_minutes || 0}</span>
              </div>
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-success">&#128197;</span>
                  <span>Daily Claims</span>
                </div>
                <span className="fw-bold text-success">{earning_breakdown?.daily_claims || 0}</span>
              </div>
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-warning">&#128247;</span>
                  <span>Campus Photos</span>
                </div>
                <span className="fw-bold text-warning">{earning_breakdown?.campus_photos || 0}</span>
              </div>
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-info">&#128101;</span>
                  <span>Daily Engagement</span>
                </div>
                <span className="fw-bold text-info">{earning_breakdown?.daily_engagement || 0}</span>
              </div>
              <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                <div className="d-flex align-items-center gap-2">
                  <span className="text-warning">&#127942;</span>
                  <span>Achievements</span>
                </div>
                <span className="fw-bold text-warning">{earning_breakdown?.achievements || 0}</span>
              </div>
              {earning_breakdown?.verification_bonus > 0 && (
                <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="text-success">&#9989;</span>
                    <span>Verification Bonus</span>
                  </div>
                  <span className="fw-bold text-success">{earning_breakdown.verification_bonus}</span>
                </div>
              )}
              {earning_breakdown?.onboarding_bonus > 0 && (
                <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="text-primary">&#127891;</span>
                    <span>Onboarding Bonus</span>
                  </div>
                  <span className="fw-bold text-primary">{earning_breakdown.onboarding_bonus}</span>
                </div>
              )}
              {earning_breakdown?.enrollment_deposit > 0 && (
                <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="text-purple">&#127979;</span>
                    <span>Enrollment Deposit</span>
                  </div>
                  <span className="fw-bold text-purple">{earning_breakdown.enrollment_deposit}</span>
                </div>
              )}
              {earning_breakdown?.birthday_bonus > 0 && (
                <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="text-pink">&#127874;</span>
                    <span>Birthday Bonus</span>
                  </div>
                  <span className="fw-bold text-pink">{earning_breakdown.birthday_bonus}</span>
                </div>
              )}
              {earning_breakdown?.boost_bonus > 0 && (
                <div className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                  <div className="d-flex align-items-center gap-2">
                    <span className="text-purple">&#128640;</span>
                    <span>Server Boost Bonus</span>
                  </div>
                  <span className="fw-bold text-purple">{earning_breakdown.boost_bonus}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <div className="border rounded bg-white p-4 h-100">
            <h2 className="h5 fw-bold mb-4 d-flex align-items-center gap-2">
              <span className="text-danger">&#10134;</span>
              Points Spent Breakdown
            </h2>
            {spending_breakdown && Object.keys(spending_breakdown).length > 0 ? (
              <div className="d-flex flex-column gap-2">
                {Object.entries(spending_breakdown).map(([type, amount]) => (
                  <div key={type} className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                    <div className="d-flex align-items-center gap-2">
                      {type === "physical" && <span className="text-primary">&#128230;</span>}
                      {type === "role" && <span className="text-purple">&#128100;</span>}
                      {type === "minecraft_skin" && <span className="text-success">&#129513;</span>}
                      {type === "game_code" && <span className="text-warning">&#127918;</span>}
                      {!["physical", "role", "minecraft_skin", "game_code"].includes(type) && (
                        <span className="text-muted">&#128722;</span>
                      )}
                      <span className="text-capitalize">{type.replace("_", " ")}</span>
                    </div>
                    <span className="fw-bold text-danger">{amount}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-5 text-muted">
                <div className="display-4 mb-2">&#128722;</div>
                <p className="mb-0">No purchases yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {achievements && achievements.length > 0 && (
        <div className="border rounded bg-white p-4 mb-4">
          <h2 className="h5 fw-bold mb-4 d-flex align-items-center gap-2">
            <span className="text-warning">&#127942;</span>
            Achievements ({achievements.length})
          </h2>
          <div className="row g-3">
            {achievements.map((achievement) => (
              <div key={achievement.id} className="col-12 col-md-6 col-lg-4">
                <div className="border border-warning rounded p-3 bg-warning bg-opacity-10">
                  <div className="d-flex align-items-center justify-content-between mb-2">
                    <h3 className="h6 fw-semibold text-warning mb-0">{achievement.name}</h3>
                    <span className="small fw-bold text-warning">+{achievement.points}</span>
                  </div>
                  <p className="small text-muted mb-0">{achievement.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="row g-4 mb-4">
        <div className="col-12 col-lg-6">
          <div className="border rounded bg-white p-4 h-100">
            <h2 className="h5 fw-bold mb-4 d-flex align-items-center gap-2">
              <span className="text-primary">&#128722;</span>
              Recent Purchases (Last 30 Days)
            </h2>
            {recent_purchases && recent_purchases.length > 0 ? (
              <div className="d-flex flex-column gap-2">
                {recent_purchases.map((purchase) => (
                  <div key={purchase.id} className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                    <div>
                      <div className="fw-semibold">{purchase.product_name}</div>
                      <div className="small text-muted">{formatDateTime(purchase.timestamp)}</div>
                    </div>
                    <span className="fw-bold text-danger">-{purchase.points_spent}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-muted">
                <div className="display-4 mb-2">&#128722;</div>
                <p className="mb-0">No recent purchases</p>
              </div>
            )}
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <div className="border rounded bg-white p-4 h-100">
            <h2 className="h5 fw-bold mb-4 d-flex align-items-center gap-2">
              <span className="text-warning">&#11088;</span>
              Recent Achievements (Last 30 Days)
            </h2>
            {recent_achievements && recent_achievements.length > 0 ? (
              <div className="d-flex flex-column gap-2">
                {recent_achievements.map((ua, index) => (
                  <div key={index} className="d-flex align-items-center justify-content-between p-2 bg-light rounded">
                    <div>
                      <div className="fw-semibold text-warning">{ua.name}</div>
                      <div className="small text-muted">{formatDateTime(ua.achieved_at)}</div>
                    </div>
                    <span className="fw-bold text-warning">+{ua.points}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-muted">
                <div className="display-4 mb-2">&#11088;</div>
                <p className="mb-0">No recent achievements</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="border rounded bg-white p-4">
        <h2 className="h5 fw-bold mb-4 d-flex align-items-center gap-2">
          <span className="text-primary">&#128100;</span>
          User Information
        </h2>
        <div className="row g-4">
          <div className="col-12 col-md-6 col-lg-4">
            <div className="small text-muted mb-1">Discord ID</div>
            <div className="fw-semibold">{user?.discord_id || "Not set"}</div>
          </div>
          <div className="col-12 col-md-6 col-lg-4">
            <div className="small text-muted mb-1">User ID</div>
            <div className="fw-semibold">{user?.id || "N/A"}</div>
          </div>
          <div className="col-12 col-md-6 col-lg-4">
            <div className="small text-muted mb-1">Joined</div>
            <div className="fw-semibold">{formatDate(user?.created_at)}</div>
          </div>
          {user?.birthday && (
            <div className="col-12 col-md-6 col-lg-4">
              <div className="small text-muted mb-1">Birthday</div>
              <div className="fw-semibold">{user.birthday}</div>
            </div>
          )}
          <div className="col-12 col-md-6 col-lg-4">
            <div className="small text-muted mb-1">Total Purchases</div>
            <div className="fw-semibold">{stats?.total_purchases || 0}</div>
          </div>
          <div className="col-12 col-md-6 col-lg-4">
            <div className="small text-muted mb-1">Total Achievements</div>
            <div className="fw-semibold">{stats?.total_achievements || 0}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

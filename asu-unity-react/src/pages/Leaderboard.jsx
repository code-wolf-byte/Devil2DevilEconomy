import React from "react";
import { Button } from "@asu/unity-react-core";

export default function Leaderboard() {
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [users, setUsers] = React.useState([]);
  const [totals, setTotals] = React.useState(null);

  const apiBaseUrl = React.useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  React.useEffect(() => {
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
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Leaderboard</h1>
        <p className="text-muted">Loading leaderboard...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Leaderboard</h1>
        <p className="text-danger">Failed to load leaderboard: {status.error}</p>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="border rounded bg-white p-4 text-center mb-4">
        <h1 className="h3 fw-bold mb-1">Leaderboard</h1>
        <p className="text-muted mb-0">Top users by point balance</p>
      </div>

      <div className="border rounded bg-white p-4">
        {users.length ? (
          <div className="d-flex flex-column gap-3">
            {users.map((user, index) => (
              <div
                key={user.id}
                className="border rounded p-3 d-flex align-items-center gap-3"
                style={{
                  background:
                    index === 0
                      ? "rgba(255, 193, 7, 0.1)"
                      : index === 1
                      ? "rgba(108, 117, 125, 0.1)"
                      : index === 2
                      ? "rgba(255, 159, 67, 0.12)"
                      : "#f8f9fa",
                }}
              >
                <div
                  className="rounded-circle d-flex align-items-center justify-content-center fw-bold text-white"
                  style={{
                    width: "48px",
                    height: "48px",
                    background:
                      index === 0
                        ? "#f0ad4e"
                        : index === 1
                        ? "#adb5bd"
                        : index === 2
                        ? "#fd7e14"
                        : "#6c757d",
                  }}
                >
                  {index + 1}
                </div>
                <img
                  src={user.avatar_url}
                  alt={user.username}
                  className="rounded-circle"
                  style={{ width: "48px", height: "48px", objectFit: "cover" }}
                />
                <div className="flex-grow-1">
                  <div className="fw-semibold">{user.username}</div>
                  <div className="text-muted small">
                    {user.points} total points earned
                  </div>
                </div>
                <div className="text-end">
                  <div className="fw-bold text-warning d-flex align-items-center gap-2 justify-content-end">
                    <img
                      src="/static/Coin_Gold.png"
                      alt="Balance"
                      style={{ width: "18px", height: "18px" }}
                    />
                    {user.balance}
                  </div>
                  <div className="text-muted small">points</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-muted py-5">
            No users yet. Be the first to join and start earning points!
          </div>
        )}
      </div>

      {totals ? (
        <div className="row g-3 g-md-4 mt-4">
          <div className="col-12 col-md-4">
            <div className="border rounded bg-white p-4 text-center">
              <div className="text-muted">Total Users</div>
              <div className="h3 fw-bold text-primary mb-0">
                {totals.total_users}
              </div>
            </div>
          </div>
          <div className="col-12 col-md-4">
            <div className="border rounded bg-white p-4 text-center">
              <div className="text-muted">Total Points</div>
              <div className="h3 fw-bold text-warning mb-0 d-flex align-items-center justify-content-center gap-2">
                <img
                  src="/static/Coin_Gold.png"
                  alt="Total points"
                  style={{ width: "20px", height: "20px" }}
                />
                {totals.total_balance}
              </div>
            </div>
          </div>
          <div className="col-12 col-md-4">
            <div className="border rounded bg-white p-4 text-center">
              <div className="text-muted">Points Earned</div>
              <div className="h3 fw-bold text-success mb-0">
                {totals.total_points}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-4">
        <Button label="Back to Store" color="gray" href="/store" />
      </div>
    </div>
  );
}

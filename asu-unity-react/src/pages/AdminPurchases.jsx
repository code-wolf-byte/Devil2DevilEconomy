import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function AdminPurchases({
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
        ? `${apiBaseUrl}/api/admin/purchases?page=${page}`
        : `/api/admin/purchases?page=${page}`;
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        throw new Error(`Failed to load purchases (${response.status})`);
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
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleDateString();
  };

  const formatTime = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
        <Button label="Back to Dashboard" color="gray" href="/dashboard" />
      </div>
    );
  }

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <div className="text-center py-5">
          <div className="spinner-border text-warning mb-3" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted">Loading purchase data...</p>
        </div>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <div className="alert alert-danger">{status.error}</div>
        <Button label="Retry" color="gold" onClick={() => loadData(currentPage)} />
      </div>
    );
  }

  const { purchases, stats, pagination } = data || {};

  return (
    <div className="container py-5">
      <div className="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-1">Purchase History</h1>
          <p className="text-muted mb-0">View all user purchases and transactions</p>
        </div>
        <Button label="Back to Admin Panel" color="gray" href="/dashboard" />
      </div>

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-3 text-center">
            <div className="h4 fw-bold text-warning mb-1">{pagination?.total || 0}</div>
            <div className="small text-muted">Total Purchases</div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-3 text-center">
            <div className="h4 fw-bold text-success mb-1">{stats?.total_points_on_page || 0}</div>
            <div className="small text-muted">Points on Page</div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-3 text-center">
            <div className="h4 fw-bold text-primary mb-1">{pagination?.page || 1}</div>
            <div className="small text-muted">Current Page</div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="border rounded bg-white p-3 text-center">
            <div className="h4 fw-bold text-purple mb-1">{pagination?.pages || 1}</div>
            <div className="small text-muted">Total Pages</div>
          </div>
        </div>
      </div>

      {purchases && purchases.length > 0 ? (
        <>
          <div className="d-none d-md-block border rounded bg-white overflow-hidden mb-4">
            <div className="bg-light px-4 py-3 border-bottom">
              <h3 className="h6 fw-semibold mb-0">Purchase Records</h3>
            </div>
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead className="table-light">
                  <tr>
                    <th className="text-muted small text-uppercase">User</th>
                    <th className="text-muted small text-uppercase">Product</th>
                    <th className="text-muted small text-uppercase">Points</th>
                    <th className="text-muted small text-uppercase">Date</th>
                    <th className="text-muted small text-uppercase">UUID</th>
                  </tr>
                </thead>
                <tbody>
                  {purchases.map((purchase) => (
                    <tr key={purchase.id}>
                      <td>
                        <div className="d-flex align-items-center gap-2">
                          {purchase.user.avatar_url ? (
                            <img
                              src={purchase.user.avatar_url}
                              alt={purchase.user.username}
                              className="rounded-circle border border-warning"
                              style={{ width: "32px", height: "32px", objectFit: "cover" }}
                            />
                          ) : (
                            <div
                              className="rounded-circle bg-light border border-warning d-flex align-items-center justify-content-center"
                              style={{ width: "32px", height: "32px" }}
                            >
                              <span className="text-warning small">U</span>
                            </div>
                          )}
                          <div>
                            <div className="fw-medium small">{purchase.user.username}</div>
                            <div className="text-muted small">ID: {purchase.user.discord_id}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="d-flex align-items-center gap-2">
                          {purchase.product.image_url ? (
                            <img
                              src={purchase.product.image_url}
                              alt={purchase.product.name}
                              className="rounded"
                              style={{ width: "40px", height: "40px", objectFit: "cover" }}
                            />
                          ) : (
                            <div
                              className="rounded bg-light d-flex align-items-center justify-content-center text-muted"
                              style={{ width: "40px", height: "40px" }}
                            >
                              &#128230;
                            </div>
                          )}
                          <div>
                            <div className="fw-medium small">{purchase.product.name}</div>
                            <div className="text-muted small">{purchase.product.description}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="fw-medium text-warning d-flex align-items-center gap-1">
                          <img src="/static/Coin_Gold.png" alt="" style={{ width: "14px", height: "14px" }} />
                          {purchase.points_spent}
                        </span>
                      </td>
                      <td>
                        <div className="small">{formatDate(purchase.timestamp)}</div>
                        <div className="text-muted small">{formatTime(purchase.timestamp)}</div>
                      </td>
                      <td>
                        {purchase.user.user_uuid ? (
                          <code className="small bg-dark text-success px-2 py-1 rounded">
                            {purchase.user.user_uuid.substring(0, 8)}...
                          </code>
                        ) : (
                          <span className="text-muted small">No UUID</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="d-md-none d-flex flex-column gap-3 mb-4">
            {purchases.map((purchase) => (
              <div key={purchase.id} className="border rounded bg-white p-3">
                <div className="d-flex align-items-start justify-content-between mb-3">
                  <div className="d-flex align-items-center gap-2">
                    {purchase.user.avatar_url ? (
                      <img
                        src={purchase.user.avatar_url}
                        alt={purchase.user.username}
                        className="rounded-circle border border-warning"
                        style={{ width: "40px", height: "40px", objectFit: "cover" }}
                      />
                    ) : (
                      <div
                        className="rounded-circle bg-light border border-warning d-flex align-items-center justify-content-center"
                        style={{ width: "40px", height: "40px" }}
                      >
                        <span className="text-warning">U</span>
                      </div>
                    )}
                    <div>
                      <div className="fw-semibold">{purchase.user.username}</div>
                      <div className="text-muted small">{formatDate(purchase.timestamp)} {formatTime(purchase.timestamp)}</div>
                    </div>
                  </div>
                  <div className="text-end">
                    <div className="h5 fw-bold text-warning mb-0 d-flex align-items-center gap-1">
                      <img src="/static/Coin_Gold.png" alt="" style={{ width: "18px", height: "18px" }} />
                      {purchase.points_spent}
                    </div>
                  </div>
                </div>

                <div className="d-flex align-items-center gap-2 mb-2">
                  {purchase.product.image_url ? (
                    <img
                      src={purchase.product.image_url}
                      alt={purchase.product.name}
                      className="rounded"
                      style={{ width: "48px", height: "48px", objectFit: "cover" }}
                    />
                  ) : (
                    <div
                      className="rounded bg-light d-flex align-items-center justify-content-center text-muted"
                      style={{ width: "48px", height: "48px" }}
                    >
                      &#128230;
                    </div>
                  )}
                  <div className="flex-grow-1">
                    <div className="fw-medium">{purchase.product.name}</div>
                    <div className="text-muted small">{purchase.product.description}</div>
                  </div>
                </div>

                {purchase.user.user_uuid && (
                  <div className="mt-2 p-2 bg-light rounded">
                    <div className="text-muted small mb-1">UUID:</div>
                    <code className="small text-success">{purchase.user.user_uuid}</code>
                  </div>
                )}
              </div>
            ))}
          </div>

          {pagination && pagination.pages > 1 && (
            <div className="border rounded bg-white p-3">
              <div className="d-flex flex-column flex-md-row align-items-center justify-content-between gap-3">
                <div className="text-muted small">
                  Showing {((pagination.page - 1) * pagination.per_page) + 1} to{" "}
                  {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} purchases
                </div>

                <div className="d-flex align-items-center gap-2">
                  {pagination.has_prev && (
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => handlePageChange(1)}
                    >
                      &#x00AB;
                    </button>
                  )}

                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    disabled={!pagination.has_prev}
                    onClick={() => handlePageChange(pagination.prev_num)}
                  >
                    &#x2039;
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
                    &#x203A;
                  </button>

                  {pagination.has_next && (
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => handlePageChange(pagination.pages)}
                    >
                      &#x00BB;
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="border rounded bg-white p-5 text-center">
          <div className="display-1 text-muted mb-3">&#128717;</div>
          <h3 className="h5 fw-semibold mb-2">No Purchases Found</h3>
          <p className="text-muted">No purchase history available yet.</p>
        </div>
      )}
    </div>
  );
}

import React from "react";
import { Button } from "@asu/unity-react-core";

export default function Dashboard({
  isAuthenticated = false,
  isAdmin = false,
  userName = "",
  loginHref = "/auth/login",
  storeHref = "/store",
}) {
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [dashboardData, setDashboardData] = React.useState(null);
  const [products, setProducts] = React.useState([]);
  const [productsStatus, setProductsStatus] = React.useState({
    loading: true,
    error: null,
  });

  const apiBaseUrl = React.useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  React.useEffect(() => {
    let isMounted = true;
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      setDashboardData(null);
      setProducts([]);
      setProductsStatus({ loading: false, error: null });
      return;
    }

    const loadDashboard = async () => {
      try {
        const url = apiBaseUrl ? `${apiBaseUrl}/api/dashboard` : "/api/dashboard";
        const response = await fetch(url, {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error(`Dashboard request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setDashboardData(data);
          setStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) {
          setStatus({ loading: false, error: error.message });
        }
      }
    };

    loadDashboard();
    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl, isAuthenticated, isAdmin]);

  React.useEffect(() => {
    let isMounted = true;
    if (!isAuthenticated || !isAdmin) {
      setProducts([]);
      setProductsStatus({ loading: false, error: null });
      return;
    }

    const loadProducts = async () => {
      try {
        setProductsStatus({ loading: true, error: null });
        const url = apiBaseUrl
          ? `${apiBaseUrl}/api/admin/products`
          : "/api/admin/products";
        const response = await fetch(url, { credentials: "include" });
        if (!response.ok) {
          throw new Error(`Products request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setProducts(Array.isArray(data.products) ? data.products : []);
          setProductsStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) {
          setProductsStatus({ loading: false, error: error.message });
        }
      }
    };

    loadProducts();
    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl, isAuthenticated, isAdmin]);

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <p className="text-danger">
          You do not have permission to view this page.
        </p>
        <Button label="Back to Store" color="gray" href={storeHref} />
      </div>
    );
  }

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <p className="text-muted">Loading dashboard data...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <p className="text-danger">Failed to load dashboard: {status.error}</p>
        <Button label="Back to Store" color="gray" href={storeHref} />
      </div>
    );
  }

  const achievements = dashboardData?.achievements || [];
  const recentPurchases = dashboardData?.recent_purchases || [];
  const dashboardUser = dashboardData?.user || {};

  const achievementsCount = achievements.length;
  const purchasesCount = recentPurchases.length;

  const formatTimestamp = (value) => {
    if (!value) return "";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString();
  };

  return (
    <div className="container py-5">
      <div className="border rounded bg-white p-4 p-md-5 mb-4">
        <div className="d-flex align-items-center gap-3">
          {dashboardUser.avatar_url ? (
            <img
              src={dashboardUser.avatar_url}
              alt={dashboardUser.username || userName || "User avatar"}
              className="rounded-circle"
              style={{ width: "64px", height: "64px", objectFit: "cover" }}
            />
          ) : (
            <div
              className="rounded-circle bg-light d-flex align-items-center justify-content-center"
              style={{ width: "64px", height: "64px" }}
            >
              <span className="text-muted fw-bold">U</span>
            </div>
          )}
          <div>
            <h1 className="h3 fw-bold mb-1">
              Welcome back, {dashboardUser.username || userName || "Admin"}!
            </h1>
            <p className="text-muted mb-0">Here&apos;s your economy overview.</p>
          </div>
          <div className="ms-auto">
            <Button label="Back to Store" color="gray" href={storeHref} />
          </div>
        </div>
      </div>

      <div className="row g-3 g-lg-4 mb-4">
        <div className="col-12 col-md-6 col-lg-3">
          <div className="border rounded bg-white p-4 h-100">
            <p className="text-muted small mb-1">Current Balance</p>
            <p className="h3 fw-bold text-warning mb-0 d-flex align-items-center gap-2">
              <img
                src="/static/Coin_Gold.png"
                alt="Balance"
                style={{ width: "22px", height: "22px" }}
              />
              {dashboardUser.balance ?? 0}
            </p>
          </div>
        </div>
        <div className="col-12 col-md-6 col-lg-3">
          <div className="border rounded bg-white p-4 h-100">
            <p className="text-muted small mb-1">Total Points Earned</p>
            <p className="h3 fw-bold text-success mb-0">
              {dashboardUser.points ?? 0}
            </p>
          </div>
        </div>
        <div className="col-12 col-md-6 col-lg-3">
          <div className="border rounded bg-white p-4 h-100">
            <p className="text-muted small mb-1">Messages Sent</p>
            <p className="h3 fw-bold text-primary mb-0">
              {dashboardUser.message_count ?? 0}
            </p>
          </div>
        </div>
        <div className="col-12 col-md-6 col-lg-3">
          <div className="border rounded bg-white p-4 h-100">
            <p className="text-muted small mb-1">Voice Minutes</p>
            <p className="h3 fw-bold text-info mb-0">
              {dashboardUser.voice_minutes ?? 0}
            </p>
          </div>
        </div>
      </div>

      <div className="row g-3 g-lg-4">
        <div className="col-12 col-lg-6">
          <div className="border rounded bg-white p-4 h-100">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h2 className="h4 fw-bold mb-0">Achievements</h2>
              <span className="text-warning fw-semibold">
                {achievementsCount} Unlocked
              </span>
            </div>
            {achievements.length ? (
              <div className="d-flex flex-column gap-3">
                {achievements.map((achievement) => (
                  <div
                    className="border rounded p-3 bg-light"
                    key={achievement.id}
                  >
                    <h3 className="h6 fw-bold mb-1">{achievement.name}</h3>
                    <p className="text-muted mb-1">
                      {achievement.description}
                    </p>
                    <p className="text-warning fw-semibold mb-0">
                      +{achievement.points} points
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-muted py-4">
                No achievements unlocked yet. Keep participating to earn
                achievements!
              </div>
            )}
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <div className="border rounded bg-white p-4 h-100">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h2 className="h4 fw-bold mb-0">Recent Purchases</h2>
              <Button label="Shop" color="gold" href={storeHref} size="small" />
            </div>
            {recentPurchases.length ? (
              <div className="d-flex flex-column gap-3">
                {recentPurchases.map((purchase) => (
                  <div
                    className="border rounded p-3 d-flex align-items-center gap-3 bg-light"
                    key={purchase.id}
                  >
                    {purchase.image_url ? (
                      <img
                        src={purchase.image_url}
                        alt={purchase.product_name}
                        className="rounded"
                        style={{ width: "48px", height: "48px", objectFit: "cover" }}
                      />
                    ) : (
                      <div
                        className="rounded bg-secondary-subtle d-flex align-items-center justify-content-center text-muted"
                        style={{ width: "48px", height: "48px" }}
                      >
                        📦
                      </div>
                    )}
                    <div className="flex-grow-1">
                      <h3 className="h6 fw-bold mb-1">{purchase.product_name}</h3>
                      <p className="text-muted mb-1">
                        {formatTimestamp(purchase.timestamp)}
                      </p>
                      <p className="text-danger fw-semibold mb-0">
                        -{purchase.points_spent} points
                      </p>
                      {purchase.download_url ? (
                        <a
                          href={purchase.download_url}
                          className="btn btn-sm btn-success mt-2"
                        >
                          Download
                        </a>
                      ) : purchase.product_type === "minecraft_skin" ? (
                        <p className="text-muted small mt-2 mb-0">
                          Processing download...
                        </p>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-muted py-4">
                No purchases yet. Visit the shop to buy your first item!
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="border rounded bg-white p-4 mt-4">
        <h2 className="h4 fw-bold mb-3">Quick Actions</h2>
        <div className="d-flex flex-column flex-md-row gap-3">
          <Button label="Visit Shop" color="gold" href={storeHref} />
          <Button label="View Leaderboard" color="gray" href="/leaderboard" />
          <Button label="Manage Products" color="gray" href="/admin/products" />
        </div>
      </div>

      <div className="border rounded bg-white p-4 mt-4">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-3">
          <h2 className="h4 fw-bold mb-0">Products</h2>
          <Button label="Add Product" color="gold" href="/admin/products/new" />
        </div>
        {productsStatus.error ? (
          <div className="alert alert-danger">{productsStatus.error}</div>
        ) : null}
        {productsStatus.loading ? (
          <p className="text-muted mb-0">Loading products...</p>
        ) : products.length ? (
          <div className="list-group">
            {products.map((product) => (
              <a
                key={product.id}
                href={`/admin/products/${product.id}`}
                className="list-group-item list-group-item-action d-flex align-items-center gap-3"
              >
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="rounded"
                    style={{ width: "44px", height: "44px", objectFit: "cover" }}
                  />
                ) : (
                  <div
                    className="rounded bg-light d-flex align-items-center justify-content-center"
                    style={{ width: "44px", height: "44px" }}
                  >
                    📦
                  </div>
                )}
                <div className="flex-grow-1">
                  <div className="fw-semibold">{product.name}</div>
                  <div className="small text-muted">
                    {product.is_active ? "Active" : "Archived"} ·{" "}
                    {product.price} pts
                  </div>
                </div>
              </a>
            ))}
          </div>
        ) : (
          <p className="text-muted mb-0">No products yet.</p>
        )}
      </div>
    </div>
  );
}

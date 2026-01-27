import React from "react";
import { Button } from "@asu/unity-react-core";

export default function MyPurchases({
  isAuthenticated = false,
  loginHref = "/auth/login",
}) {
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [purchases, setPurchases] = React.useState([]);

  const apiBaseUrl = React.useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  React.useEffect(() => {
    let isMounted = true;
    if (!isAuthenticated) {
      setStatus({ loading: false, error: null });
      setPurchases([]);
      return;
    }

    const loadPurchases = async () => {
      try {
        const url = apiBaseUrl ? `${apiBaseUrl}/api/my-purchases` : "/api/my-purchases";
        const response = await fetch(url, { credentials: "include" });
        if (!response.ok) {
          throw new Error(`Purchases request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setPurchases(Array.isArray(data.purchases) ? data.purchases : []);
          setStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) {
          setStatus({ loading: false, error: error.message });
        }
      }
    };

    loadPurchases();
    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl, isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">My Purchases</h1>
        <p className="text-muted">Please sign in to view your purchases.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">My Purchases</h1>
        <p className="text-muted">Loading purchase history...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">My Purchases</h1>
        <p className="text-danger">Failed to load purchases: {status.error}</p>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="text-center mb-4">
        <h1 className="display-6 fw-bold mb-2">My Purchases</h1>
        <p className="text-muted">
          View your purchase history and track your orders.
        </p>
      </div>

      {purchases.length ? (
        <>
          <div className="border rounded bg-white p-4">
            <div className="table-responsive">
              <table className="table align-middle">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Price</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {purchases.map((purchase) => (
                    <tr key={purchase.id}>
                      <td>
                        <div className="d-flex align-items-center gap-3">
                          {purchase.image_url ? (
                            <img
                              src={purchase.image_url}
                              alt={purchase.product_name}
                              className="rounded"
                              style={{ width: "48px", height: "48px", objectFit: "cover" }}
                            />
                          ) : (
                            <div
                              className="rounded bg-light d-flex align-items-center justify-content-center"
                              style={{ width: "48px", height: "48px" }}
                            >
                              📦
                            </div>
                          )}
                          <div>
                            <div className="fw-semibold">{purchase.product_name}</div>
                            <div className="text-muted small">
                              {(purchase.product_description || "").slice(0, 50)}
                              {(purchase.product_description || "").length > 50
                                ? "..."
                                : ""}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="fw-semibold text-warning">
                        <div className="d-flex align-items-center gap-2">
                          <img
                            src="/static/Coin_Gold.png"
                            alt="Price"
                            style={{ width: "16px", height: "16px" }}
                          />
                          {purchase.points_spent}
                        </div>
                      </td>
                      <td className="text-muted">
                        {new Date(purchase.timestamp).toLocaleString()}
                      </td>
                      <td>
                        {purchase.product_type === "minecraft_skin" ? (
                          <span className="badge text-bg-success">Digital Download</span>
                        ) : (
                          <span className="badge text-bg-warning">Pending Pickup</span>
                        )}
                      </td>
                      <td>
                        {purchase.download_url ? (
                          <a
                            href={purchase.download_url}
                            className="btn btn-sm btn-success"
                          >
                            Download
                          </a>
                        ) : purchase.product_type === "minecraft_skin" ? (
                          <span className="text-muted small">Processing...</span>
                        ) : (
                          <span className="text-muted small">Physical Item</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="border rounded bg-white p-4 mt-4">
            <h2 className="h4 fw-bold mb-3">Item Pickup Information</h2>
            <p className="text-muted">
              All purchased items can be collected during the Devil2Devil
              in-person event during Welcome Week in the upcoming fall semester.
            </p>
            <div className="row g-3 mt-3">
              <div className="col-12 col-md-6">
                <div className="border rounded p-3 h-100">
                  <div className="fw-semibold">Event Location</div>
                  <div className="text-muted">
                    Devil2Devil in-person event during ASU Welcome Week
                  </div>
                </div>
              </div>
              <div className="col-12 col-md-6">
                <div className="border rounded p-3 h-100">
                  <div className="fw-semibold">When to Attend</div>
                  <div className="text-muted">
                    Fall semester Welcome Week (exact dates will be announced)
                  </div>
                </div>
              </div>
              <div className="col-12 col-md-6">
                <div className="border rounded p-3 h-100">
                  <div className="fw-semibold">What to Bring</div>
                  <div className="text-muted">
                    Your student ID and Discord username for item verification
                  </div>
                </div>
              </div>
              <div className="col-12 col-md-6">
                <div className="border rounded p-3 h-100">
                  <div className="fw-semibold">Need Help?</div>
                  <div className="text-muted">
                    Contact admins in Discord if you have questions about your purchases
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="border rounded bg-white p-4 text-center">
          <div className="display-6 mb-3">🛍️</div>
          <h2 className="h5 fw-bold mb-2">No Purchases Yet</h2>
          <p className="text-muted">
            You haven&apos;t made any purchases yet. Start shopping to see your
            order history here!
          </p>
          <Button label="Browse Store" color="gold" href="/store" />
        </div>
      )}
    </div>
  );
}

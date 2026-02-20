import React, { useEffect, useMemo, useState } from "react";
import { Button, Divider, Image } from "@asu/unity-react-core";

const VIDEO_EXTENSIONS = [".mov", ".mp4", ".webm", ".ogg", ".avi"];

function isVideoUrl(url) {
  if (!url) return false;
  const lowerUrl = url.toLowerCase();
  return VIDEO_EXTENSIONS.some((ext) => lowerUrl.endsWith(ext));
}

export default function Product({ productId, isAuthenticated = false, loginHref = "/auth/login" }) {
  const [product, setProduct] = useState(null);
  const [status, setStatus] = useState({ loading: true, error: null });
  const [activeMediaIndex, setActiveMediaIndex] = useState(0);
  const [purchaseStatus, setPurchaseStatus] = useState({
    loading: false,
    error: null,
    success: null,
  });
  const [showConfirm, setShowConfirm] = useState(false);

  const apiBaseUrl = useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  const withBase = (path) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path);

  useEffect(() => {
    let isMounted = true;

    const loadProduct = async () => {
      try {
        const response = await fetch(withBase(`/api/product/${productId}`));
        if (!response.ok) {
          throw new Error(`Product request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setProduct(data.product || null);
          setStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) {
          setStatus({ loading: false, error: error.message });
        }
      }
    };

    loadProduct();
    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl, productId]);

  const media = useMemo(() => {
    if (product?.media?.length) {
      return product.media.map((item) => ({
        ...item,
        type: isVideoUrl(item.url) ? "video" : item.type,
      }));
    }
    if (product?.image_url) {
      return [
        {
          id: "fallback",
          type: isVideoUrl(product.image_url) ? "video" : "image",
          url: product.image_url,
          alt_text: product.name,
          is_primary: true,
        },
      ];
    }
    return [];
  }, [product]);

  useEffect(() => {
    if (media.length === 0) {
      setActiveMediaIndex(0);
      return;
    }
    const primaryIndex = media.findIndex((item) => item.is_primary);
    setActiveMediaIndex(primaryIndex === -1 ? 0 : primaryIndex);
  }, [media]);

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Product</h1>
        <p className="text-muted">Loading product details...</p>
      </div>
    );
  }

  if (status.error || !product) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Product</h1>
        <p className="text-danger">
          Failed to load product: {status.error || "Not found"}
        </p>
        <div className="mt-3">
          <Button label="Back to store" color="gray" href="/store" size="small" />
        </div>
      </div>
    );
  }

  const handlePurchase = () => {
    if (!isAuthenticated) {
      window.location.href = loginHref;
      return;
    }
    setPurchaseStatus({ loading: false, error: null, success: null });
    setShowConfirm(true);
  };

  const confirmPurchase = async () => {
    setShowConfirm(false);
    setPurchaseStatus({ loading: true, error: null, success: null });
    try {
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/purchase/${productId}`
        : `/api/purchase/${productId}`;
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.message || `Purchase failed (${response.status})`);
      }
      setPurchaseStatus({
        loading: false,
        error: null,
        success: data.message || "Purchase completed.",
      });
    } catch (error) {
      setPurchaseStatus({
        loading: false,
        error: error.message,
        success: null,
      });
    }
  };

  const activeMedia = media[activeMediaIndex];

  return (
    <div className="container py-5 product-page">
      <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-2">{product.name}</h1>
        </div>
        <Button label="Back to store" color="gray" href="/store" size="small" />
      </div>

      <Divider />

      <div className="row g-4 mt-2">
        <div className="col-12 col-lg-7">
          <div className="product-media border rounded p-3 h-100">
            {media.length === 0 ? (
              <div className="text-muted">No media available.</div>
            ) : media.length === 1 ? (
              activeMedia.type === "video" ? (
                <video
                  className="w-100 rounded"
                  controls
                  src={activeMedia.url}
                />
              ) : (
                <Image
                  src={activeMedia.url}
                  alt={activeMedia.alt_text || product.name}
                  cssClasses={["img-fluid", "rounded", "w-100"]}
                />
              )
            ) : (
              <>
                <div
                  id="productCarousel"
                  className="carousel slide"
                  data-bs-ride="false"
                >
                  <div className="carousel-inner rounded">
                    {media.map((item, index) => (
                      <div
                        key={item.id || `${item.type}-${index}`}
                        className={`carousel-item${index === activeMediaIndex ? " active" : ""}`}
                      >
                        {item.type === "video" ? (
                          <video
                            className="d-block w-100 rounded"
                            controls
                            src={item.url}
                          />
                        ) : (
                          <img
                            className="d-block w-100 rounded"
                            src={item.url}
                            alt={item.alt_text || product.name}
                            style={{ objectFit: "cover", aspectRatio: "1/1" }}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                  <button
                    className="carousel-control-prev"
                    type="button"
                    data-bs-target="#productCarousel"
                    data-bs-slide="prev"
                    onClick={() =>
                      setActiveMediaIndex((prev) =>
                        prev === 0 ? media.length - 1 : prev - 1
                      )
                    }
                  >
                    <span className="carousel-control-prev-icon" aria-hidden="true" />
                    <span className="visually-hidden">Previous</span>
                  </button>
                  <button
                    className="carousel-control-next"
                    type="button"
                    data-bs-target="#productCarousel"
                    data-bs-slide="next"
                    onClick={() =>
                      setActiveMediaIndex((prev) =>
                        prev === media.length - 1 ? 0 : prev + 1
                      )
                    }
                  >
                    <span className="carousel-control-next-icon" aria-hidden="true" />
                    <span className="visually-hidden">Next</span>
                  </button>
                </div>
                <div className="d-flex flex-wrap gap-2 mt-3 justify-content-center">
                  {media.map((item, index) => (
                    <button
                      type="button"
                      key={item.id || `thumb-${index}`}
                      className="btn p-0 border rounded overflow-hidden"
                      style={{
                        width: "56px",
                        height: "56px",
                        opacity: index === activeMediaIndex ? 1 : 0.5,
                        outline: index === activeMediaIndex ? "2px solid #8C1D40" : "none",
                      }}
                      onClick={() => setActiveMediaIndex(index)}
                    >
                      {item.type === "video" ? (
                        <div
                          className="d-flex align-items-center justify-content-center bg-dark text-white"
                          style={{ width: "100%", height: "100%", fontSize: "1.2rem" }}
                        >
                          &#9654;
                        </div>
                      ) : (
                        <img
                          src={item.url}
                          alt={item.alt_text || `Thumbnail ${index + 1}`}
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      )}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="col-12 col-lg-5">
          <div className="border rounded p-4 h-100 bg-white">
            <div className="d-flex align-items-center gap-2 mb-3">
              <img
                src="/static/Coin_Gold.png"
                alt="Price"
                style={{ width: "20px", height: "20px" }}
              />
              <span className="h4 fw-bold mb-0">{product.price}</span>
            </div>
            <p className="text-muted">{product.description || "No description."}</p>
            <Divider />
            <div className="d-flex justify-content-between align-items-center">
              <span className="text-uppercase text-muted small">Stock</span>
              <span className="fw-semibold">
                {product.is_unlimited
                  ? "Unlimited"
                  : product.in_stock
                  ? `${product.stock} available`
                  : "Out of stock"}
              </span>
            </div>

            {purchaseStatus.error ? (
              <div className="alert alert-danger mt-3">
                {purchaseStatus.error}
              </div>
            ) : null}
            {purchaseStatus.success ? (
              <div className="alert alert-success mt-3">
                {purchaseStatus.success}
              </div>
            ) : null}

            <div className="mt-3 d-grid gap-2">
              <Button
                label={
                  purchaseStatus.loading
                    ? "Processing..."
                    : isAuthenticated
                    ? "Purchase"
                    : "Sign in to Purchase"
                }
                color="gold"
                disabled={purchaseStatus.loading || !product.in_stock}
                onClick={handlePurchase}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Purchase confirmation modal */}
      {showConfirm && (
        <div
          className="modal d-block"
          style={{ background: "rgba(0,0,0,0.55)" }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowConfirm(false); }}
        >
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header border-0 pb-0">
                <h5 className="modal-title fw-bold">Confirm Purchase</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowConfirm(false)}
                />
              </div>
              <div className="modal-body pt-2">
                <div className="d-flex gap-3 align-items-center mb-4">
                  {media[0]?.url && (
                    media[0].type === "video" ? (
                      <video
                        src={media[0].url}
                        muted
                        style={{ width: "80px", height: "80px", objectFit: "cover", borderRadius: "8px", flexShrink: 0 }}
                      />
                    ) : (
                      <img
                        src={media[0].url}
                        alt={product.name}
                        style={{ width: "80px", height: "80px", objectFit: "cover", borderRadius: "8px", flexShrink: 0 }}
                      />
                    )
                  )}
                  <div>
                    <div className="fw-semibold fs-5">{product.name}</div>
                    {product.description && (
                      <div className="text-muted small mt-1" style={{ maxWidth: "260px" }}>
                        {product.description.length > 100
                          ? product.description.slice(0, 100) + "…"
                          : product.description}
                      </div>
                    )}
                  </div>
                </div>

                <div className="border rounded p-3 bg-light">
                  <div className="d-flex justify-content-between align-items-center">
                    <span className="text-muted">Price</span>
                    <span className="d-flex align-items-center gap-1 fw-bold fs-5">
                      <img src="/static/Coin_Gold.png" alt="" style={{ width: "18px", height: "18px" }} />
                      {product.price}
                    </span>
                  </div>
                </div>

                <p className="text-muted small mt-3 mb-0">
                  This will deduct <strong>{product.price} pitchforks</strong> from your balance. This action cannot be undone.
                </p>
              </div>
              <div className="modal-footer border-0 pt-0 gap-2">
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => setShowConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-warning fw-semibold px-4"
                  onClick={confirmPurchase}
                >
                  Confirm Purchase
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

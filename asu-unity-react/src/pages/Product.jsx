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
      return product.media;
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
          <Button label="Back to store" color="gray" href="/" size="small" />
        </div>
      </div>
    );
  }

  const handlePurchase = async () => {
    if (!isAuthenticated) {
      window.location.href = loginHref;
      return;
    }
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
        <Button label="Back to store" color="gray" href="/" size="small" />
      </div>

      <Divider />

      <div className="row g-4 mt-2">
        <div className="col-12 col-lg-7">
          <div className="product-media border rounded p-3 h-100">
            {activeMedia ? (
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
              <div className="text-muted">No media available.</div>
            )}

            {media.length > 1 ? (
              <div className="d-flex flex-wrap gap-2 mt-3">
                {media.map((item, index) => (
                  <button
                    type="button"
                    key={item.id || `${item.type}-${index}`}
                    className={`btn btn-sm ${
                      index === activeMediaIndex
                        ? "btn-dark"
                        : "btn-outline-secondary"
                    }`}
                    onClick={() => setActiveMediaIndex(index)}
                  >
                    {item.type === "video" ? "Video" : "Image"} {index + 1}
                  </button>
                ))}
              </div>
            ) : null}
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
    </div>
  );
}

import React, { useEffect, useMemo, useState } from "react";
import { Button, Pagination } from "@asu/unity-react-core";
import ProductCard from "../components/ProductCard";

export default function Store({
  isAuthenticated = false,
  isAdmin = false,
  userName = "",
  balance = null,
  avatarUrl = "",
}) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [status, setStatus] = useState({ loading: true, error: null });

  const apiBaseUrl = useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  const withBase = (path) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  useEffect(() => {
    let isMounted = true;

    const loadStore = async () => {
      try {
        const [storeRes, catRes] = await Promise.all([
          fetch(withBase("/api/store")),
          fetch(withBase("/api/categories")),
        ]);
        if (!storeRes.ok) {
          throw new Error(`Store request failed (${storeRes.status})`);
        }
        const storeData = await storeRes.json();
        if (isMounted) {
          setProducts(Array.isArray(storeData.products) ? storeData.products : []);
          setStatus({ loading: false, error: null });
        }
        if (catRes.ok) {
          const catData = await catRes.json();
          if (isMounted) {
            setCategories(Array.isArray(catData.categories) ? catData.categories : []);
          }
        }
      } catch (error) {
        if (isMounted) {
          setStatus({ loading: false, error: error.message });
        }
      }
    };

    loadStore();
    return () => {
      isMounted = false;
    };
  }, [apiBaseUrl]);

  // Reset to page 1 when category filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [activeCategory]);

  const filteredProducts = useMemo(() => {
    if (activeCategory === "all") return products;
    return products.filter((p) => p.category === activeCategory);
  }, [products, activeCategory]);

  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / itemsPerPage));

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const pageProducts = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredProducts.slice(startIndex, startIndex + itemsPerPage);
  }, [currentPage, filteredProducts]);

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Store</h1>
        <p className="text-muted">Loading store inventory...</p>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Store</h1>
        <p className="text-danger">Failed to load store: {status.error}</p>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="d-flex align-items-end justify-content-between flex-wrap gap-2 mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-2">Store</h1>
          <p className="text-muted mb-0">
            Browse rewards curated for the Devil2Devil community.
          </p>
        </div>
        {!isAuthenticated ? (
          <Button
            label="Sign in with Discord"
            color="gold"
            href={withBase("/auth/login")}
            size="default"
          />
        ) : (
          <>
            <div
              className="btn btn-light d-flex align-items-center gap-2"
              role="button"
              aria-disabled="true"
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={userName || "User avatar"}
                  className="rounded-circle"
                  style={{ width: "28px", height: "28px", objectFit: "cover" }}
                />
              ) : null}
              <span className="fw-semibold">{userName || "Account"}</span>
              <span className="d-inline-flex align-items-center gap-1 text-muted small">
                <img
                  src="/static/Coin_Gold.png"
                  alt="Balance"
                  style={{ width: "16px", height: "16px" }}
                />
                {balance ?? 0}
              </span>
            </div>
            {isAdmin ? (
              <Button
                label="Admin Dashboard"
                color="gray"
                href={withBase("/dashboard")}
                size="default"
              />
            ) : null}
          </>
        )}
      </div>
      {/* Category filter tabs — only shown when categories exist */}
      {categories.length > 0 && (
        <div className="uds-tabbed-panels mb-4">
          <ul className="nav nav-tabs" role="tablist">
            <li className="nav-item" role="presentation">
              <button
                className={`nav-link${activeCategory === "all" ? " active" : ""}`}
                onClick={() => setActiveCategory("all")}
                role="tab"
                aria-selected={activeCategory === "all"}
              >
                All
              </button>
            </li>
            {categories.map((cat) => (
              <li key={cat.slug} className="nav-item" role="presentation">
                <button
                  className={`nav-link${activeCategory === cat.slug ? " active" : ""}`}
                  onClick={() => setActiveCategory(cat.slug)}
                  role="tab"
                  aria-selected={activeCategory === cat.slug}
                >
                  {cat.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {filteredProducts.length === 0 ? (
        <p className="text-muted">
          {activeCategory === "all"
            ? "No products available right now."
            : "No products in this category."}
        </p>
      ) : (
        <>
          <div className="row g-4">
            {pageProducts.map((product) => (
              <div className="col-12 col-md-6 col-lg-4" key={product.id}>
                <ProductCard product={product} />
              </div>
            ))}
          </div>
          {totalPages > 1 ? (
            <div className="d-flex justify-content-center mt-4">
              <Pagination
                type="bordered"
                background="white"
                currentPage={currentPage}
                totalPages={totalPages}
                onChange={(_, page) => setCurrentPage(page)}
              />
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

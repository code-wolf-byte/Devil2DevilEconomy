import React, { useEffect, useMemo, useState } from "react";
import { Button } from "@asu/unity-react-core";
import { Card, Pagination } from "@asu/unity-react-core";

export default function Store() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState({ loading: true, error: null });

  const apiBaseUrl = useMemo(() => {
    const value = import.meta.env.VITE_API_BASE_URL || "";
    return value ? value.replace(/\/+$/, "") : "";
  }, []);

  const withBase = (path) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  useEffect(() => {
    let isMounted = true;

    const loadStore = async () => {
      try {
        const response = await fetch(withBase("/api/store"));
        if (!response.ok) {
          throw new Error(`Store request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setProducts(Array.isArray(data.products) ? data.products : []);
          setStatus({ loading: false, error: null });
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

  const totalPages = Math.max(1, Math.ceil(products.length / itemsPerPage));

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const pageProducts = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return products.slice(startIndex, startIndex + itemsPerPage);
  }, [currentPage, products]);

  const formatTags = (product) => {
    const tags = [
      {
        label: `Price: ${product.price}`,
        color: "dark",
        ariaLabel: `Price ${product.price}`,
      },
    ];

    if (product.is_unlimited) {
      tags.push({ label: "Unlimited stock", color: "gray" });
    } else if (product.in_stock) {
      tags.push({
        label: `In stock (${product.stock})`,
        color: "gray",
        ariaLabel: `In stock ${product.stock}`,
      });
    } else {
      tags.push({ label: "Out of stock", color: "dark" });
    }

    if (product.product_type) {
      tags.push({
        label: product.product_type.replace(/_/g, " "),
        color: "white",
      });
    }

    return tags;
  };

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
        <Button
          label="Sign in with Discord"
          color="gold"
          href={withBase("/auth/login")}
          size="default"
        />
      </div>
      {products.length === 0 ? (
        <p className="text-muted">No products available right now.</p>
      ) : (
        <>
          <div className="row g-4">
            {pageProducts.map((product) => (
            <div className="col-12 col-md-6 col-lg-4" key={product.id}>
              <a
                className="text-decoration-none text-reset d-block h-100"
                href={`/product/${product.id}`}
              >
                <Card
                  type="default"
                  horizontal={false}
                  showBorders={true}
                  image={product.image_url || undefined}
                  imageAltText={product.name}
                  title={product.name}
                  body={product.description || "No description available."}
                  tags={formatTags(product)}
                />
              </a>
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

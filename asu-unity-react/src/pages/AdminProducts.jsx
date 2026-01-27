import React from "react";
import { Button } from "@asu/unity-react-core";

const PRODUCT_TYPES = [
  { value: "physical", label: "Physical Product" },
  { value: "role", label: "Discord Role" },
  { value: "minecraft_skin", label: "Minecraft Skin" },
  { value: "game_code", label: "Game Code" },
  { value: "custom", label: "Custom Digital" },
];

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function AdminProducts({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [products, setProducts] = React.useState([]);
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [formStatus, setFormStatus] = React.useState({
    saving: false,
    error: null,
    success: null,
  });
  const [selectedId, setSelectedId] = React.useState(null);
  const [form, setForm] = React.useState({
    name: "",
    description: "",
    price: "",
    stock: "",
    unlimitedStock: false,
    product_type: "physical",
    image: null,
    preview_image: null,
    download_file: null,
    gallery_images: [],
    preview_video_url: "",
  });
  const [currentMedia, setCurrentMedia] = React.useState({
    image_url: null,
    preview_image_url: null,
    download_file_url: null,
    media: [],
  });

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const loadProducts = React.useCallback(async () => {
    try {
      setStatus({ loading: true, error: null });
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/products` : "/api/admin/products";
      const response = await fetch(url, { credentials: "include" });
      if (!response.ok) {
        throw new Error(`Failed to load products (${response.status})`);
      }
      const data = await response.json();
      setProducts(Array.isArray(data.products) ? data.products : []);
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
    loadProducts();
  }, [isAuthenticated, isAdmin, loadProducts]);

  React.useEffect(() => {
    const path = window.location.pathname;
    const match = path.match(/\/admin\/products\/(\d+)/);
    if (match) {
      setSelectedId(Number.parseInt(match[1], 10));
      return;
    }
    if (path.endsWith("/admin/products/new")) {
      setSelectedId(null);
    }
  }, []);

  React.useEffect(() => {
    if (!selectedId) {
      setForm({
        name: "",
        description: "",
        price: "",
        stock: "",
        unlimitedStock: false,
        product_type: "physical",
        image: null,
        preview_image: null,
        download_file: null,
        gallery_images: [],
        preview_video_url: "",
      });
      setCurrentMedia({
        image_url: null,
        preview_image_url: null,
        download_file_url: null,
        media: [],
      });
      return;
    }

    const loadProduct = async () => {
      try {
        const url = apiBaseUrl
          ? `${apiBaseUrl}/api/admin/products/${selectedId}`
          : `/api/admin/products/${selectedId}`;
        const response = await fetch(url, { credentials: "include" });
        if (!response.ok) {
          throw new Error(`Failed to load product (${response.status})`);
        }
        const data = await response.json();
        const product = data.product || {};
        setForm({
          name: product.name || "",
          description: product.description || "",
          price: product.price ?? "",
          stock: product.stock ?? "",
          unlimitedStock: product.stock === null,
          product_type: product.product_type || "physical",
          image: null,
          preview_image: null,
          download_file: null,
          gallery_images: [],
          preview_video_url: "",
        });
        setCurrentMedia({
          image_url: product.image_url || null,
          preview_image_url: product.preview_image_url || null,
          download_file_url: product.download_file_url || null,
          media: Array.isArray(product.media) ? product.media : [],
        });
      } catch (error) {
        setFormStatus((prev) => ({ ...prev, error: error.message }));
      }
    };

    loadProduct();
  }, [apiBaseUrl, selectedId]);

  const updateForm = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSelectProduct = (productId) => {
    setSelectedId(productId);
    window.history.pushState({}, "", `/admin/products/${productId}`);
  };

  const handleNewProduct = () => {
    setSelectedId(null);
    window.history.pushState({}, "", "/admin/products/new");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormStatus({ saving: true, error: null, success: null });

    try {
      const formData = new FormData();
      formData.append("name", form.name);
      formData.append("description", form.description);
      formData.append("price", form.price);
      formData.append(
        "stock",
        form.unlimitedStock ? "unlimited" : form.stock
      );
      formData.append("product_type", form.product_type);

      if (form.image) {
        formData.append("image", form.image);
      }
      if (form.preview_image) {
        formData.append("preview_image", form.preview_image);
      }
      if (form.download_file) {
        formData.append("download_file", form.download_file);
      }
      if (form.gallery_images?.length) {
        form.gallery_images.forEach((file) => {
          formData.append("gallery_images", file);
        });
      }
      if (form.preview_video_url) {
        formData.append("preview_video_url", form.preview_video_url);
      }

      const url = selectedId
        ? apiBaseUrl
          ? `${apiBaseUrl}/api/admin/products/${selectedId}`
          : `/api/admin/products/${selectedId}`
        : apiBaseUrl
        ? `${apiBaseUrl}/api/admin/products`
        : "/api/admin/products";

      const response = await fetch(url, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Save failed (${response.status})`);
      }

      const data = await response.json();
      const newId = data.product_id || selectedId;
      setFormStatus({ saving: false, error: null, success: "Saved!" });
      await loadProducts();
      if (!selectedId && newId) {
        handleSelectProduct(newId);
      }
    } catch (error) {
      setFormStatus({ saving: false, error: error.message, success: null });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Product Manager</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Product Manager</h1>
        <p className="text-danger">
          You do not have permission to view this page.
        </p>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-1">Products</h1>
          <p className="text-muted mb-0">Create and edit store products.</p>
        </div>
        <Button label="Add Product" color="gold" onClick={handleNewProduct} />
      </div>

      {status.error ? (
        <div className="alert alert-danger">{status.error}</div>
      ) : null}

      <div className="row g-4">
        <div className="col-12 col-lg-5">
          <div className="border rounded bg-white p-3">
            {status.loading ? (
              <p className="text-muted mb-0">Loading products...</p>
            ) : products.length ? (
              <div className="list-group">
                {products.map((product) => (
                  <button
                    key={product.id}
                    type="button"
                    className={`list-group-item list-group-item-action d-flex align-items-center gap-3 ${
                      selectedId === product.id ? "active" : ""
                    }`}
                    onClick={() => handleSelectProduct(product.id)}
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
                    <div className="flex-grow-1 text-start">
                      <div className="fw-semibold">{product.name}</div>
                      <div className="small text-muted">
                        {product.is_active ? "Active" : "Archived"} ·{" "}
                        {product.price} pts
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-muted mb-0">No products yet.</p>
            )}
          </div>
        </div>

        <div className="col-12 col-lg-7">
          <div className="border rounded bg-white p-4">
            <h2 className="h5 fw-bold mb-3">
              {selectedId ? "Edit Product" : "Add Product"}
            </h2>

            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label">Product Name</label>
                <input
                  className="form-control"
                  value={form.name}
                  onChange={(event) => updateForm("name", event.target.value)}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label">Description</label>
                <textarea
                  className="form-control"
                  rows="3"
                  value={form.description}
                  onChange={(event) =>
                    updateForm("description", event.target.value)
                  }
                />
              </div>
              <div className="row g-3">
                <div className="col-12 col-md-6">
                  <label className="form-label">Price (Points)</label>
                  <input
                    className="form-control"
                    type="number"
                    min="1"
                    value={form.price}
                    onChange={(event) =>
                      updateForm("price", event.target.value)
                    }
                    required
                  />
                </div>
                <div className="col-12 col-md-6">
                  <label className="form-label">Stock</label>
                  <input
                    className="form-control"
                    type="number"
                    min="0"
                    value={form.unlimitedStock ? "" : form.stock}
                    onChange={(event) =>
                      updateForm("stock", event.target.value)
                    }
                    disabled={form.unlimitedStock}
                  />
                  <div className="form-check mt-2">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="unlimitedStock"
                      checked={form.unlimitedStock}
                      onChange={(event) =>
                        updateForm("unlimitedStock", event.target.checked)
                      }
                    />
                    <label className="form-check-label" htmlFor="unlimitedStock">
                      Unlimited stock
                    </label>
                  </div>
                </div>
              </div>

              <div className="mt-3">
                <label className="form-label">Product Type</label>
                <select
                  className="form-select"
                  value={form.product_type}
                  onChange={(event) =>
                    updateForm("product_type", event.target.value)
                  }
                >
                  {PRODUCT_TYPES.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {form.product_type !== "minecraft_skin" ? (
                <div className="mt-3">
                  <label className="form-label">Product Image</label>
                  {currentMedia.image_url ? (
                    <div className="mb-2">
                      <img
                        src={currentMedia.image_url}
                        alt="Current"
                        className="rounded"
                        style={{ width: "120px", height: "120px", objectFit: "cover" }}
                      />
                    </div>
                  ) : null}
                  <input
                    className="form-control"
                    type="file"
                    accept="image/*"
                    onChange={(event) =>
                      updateForm("image", event.target.files?.[0] || null)
                    }
                  />
                </div>
              ) : (
                <>
                  <div className="mt-3">
                    <label className="form-label">Preview Image</label>
                    {currentMedia.preview_image_url ? (
                      <div className="mb-2">
                        <img
                          src={currentMedia.preview_image_url}
                          alt="Preview"
                          className="rounded"
                          style={{ width: "120px", height: "120px", objectFit: "cover" }}
                        />
                      </div>
                    ) : null}
                    <input
                      className="form-control"
                      type="file"
                      accept="image/*"
                      onChange={(event) =>
                        updateForm("preview_image", event.target.files?.[0] || null)
                      }
                    />
                  </div>
                  <div className="mt-3">
                    <label className="form-label">Download File</label>
                    {currentMedia.download_file_url ? (
                      <p className="text-muted small mb-2">
                        Current file: {currentMedia.download_file_url}
                      </p>
                    ) : null}
                    <input
                      className="form-control"
                      type="file"
                      onChange={(event) =>
                        updateForm("download_file", event.target.files?.[0] || null)
                      }
                    />
                  </div>
                  <div className="mt-3">
                    <label className="form-label">Preview Video URL</label>
                    <input
                      className="form-control"
                      type="url"
                      placeholder="https://..."
                      value={form.preview_video_url}
                      onChange={(event) =>
                        updateForm("preview_video_url", event.target.value)
                      }
                    />
                  </div>
                </>
              )}

              <div className="mt-3">
                <label className="form-label">Gallery Images</label>
                {currentMedia.media?.length ? (
                  <div className="d-flex flex-wrap gap-2 mb-2">
                    {currentMedia.media
                      .filter((item) => item.type === "image")
                      .map((item) => (
                        <img
                          key={item.id}
                          src={item.url}
                          alt={item.alt_text || "Gallery"}
                          className="rounded"
                          style={{ width: "64px", height: "64px", objectFit: "cover" }}
                        />
                      ))}
                  </div>
                ) : null}
                <input
                  className="form-control"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(event) =>
                    updateForm(
                      "gallery_images",
                      Array.from(event.target.files || [])
                    )
                  }
                />
              </div>

              {currentMedia.media?.some((item) => item.type === "video") ? (
                <div className="mt-3">
                  <label className="form-label">Existing Videos</label>
                  <div className="d-flex flex-column gap-1">
                    {currentMedia.media
                      .filter((item) => item.type === "video")
                      .map((item) => (
                        <a
                          key={item.id}
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {item.url}
                        </a>
                      ))}
                  </div>
                </div>
              ) : null}

              {formStatus.error ? (
                <div className="alert alert-danger mt-3">
                  {formStatus.error}
                </div>
              ) : null}
              {formStatus.success ? (
                <div className="alert alert-success mt-3">
                  {formStatus.success}
                </div>
              ) : null}

              <div className="d-flex gap-2 mt-3">
                <Button
                  label={formStatus.saving ? "Saving..." : "Save Product"}
                  color="gold"
                  disabled={formStatus.saving}
                />
                {selectedId ? (
                  <Button
                    label="New Product"
                    color="gray"
                    onClick={handleNewProduct}
                  />
                ) : null}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

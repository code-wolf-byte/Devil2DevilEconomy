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
    category: "general",
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
  const [categories, setCategories] = React.useState([]);

  // Category management state
  const [catNewName, setCatNewName] = React.useState("");
  const [catCreating, setCatCreating] = React.useState(false);
  const [catCreateError, setCatCreateError] = React.useState(null);
  const [catEditingId, setCatEditingId] = React.useState(null);
  const [catEditName, setCatEditName] = React.useState("");
  const [catEditError, setCatEditError] = React.useState(null);

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const withBase = React.useCallback(
    (path) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path),
    [apiBaseUrl]
  );

  const loadCategories = React.useCallback(async () => {
    try {
      const res = await fetch(withBase("/api/admin/categories"), { credentials: "include" });
      const data = await res.json();
      setCategories(Array.isArray(data.categories) ? data.categories : []);
    } catch {
      // ignore
    }
  }, [withBase]);

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
    loadCategories();
  }, [isAuthenticated, isAdmin, loadProducts, loadCategories]);

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
        category: "general",
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
          category: product.category || "general",
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
      formData.append("category", form.category || "general");

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

  const reloadCurrentMedia = React.useCallback(async () => {
    if (!selectedId) return;
    try {
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/admin/products/${selectedId}`
        : `/api/admin/products/${selectedId}`;
      const response = await fetch(url, { credentials: "include" });
      if (!response.ok) return;
      const data = await response.json();
      const product = data.product || {};
      setCurrentMedia({
        image_url: product.image_url || null,
        preview_image_url: product.preview_image_url || null,
        download_file_url: product.download_file_url || null,
        media: Array.isArray(product.media) ? product.media : [],
      });
    } catch {
      // ignore
    }
  }, [apiBaseUrl, selectedId]);

  const handleDeleteMedia = async (mediaId) => {
    if (!selectedId) return;
    try {
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/admin/products/${selectedId}/media/${mediaId}`
        : `/api/admin/products/${selectedId}/media/${mediaId}`;
      const response = await fetch(url, {
        method: "DELETE",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`Delete failed (${response.status})`);
      }
      await reloadCurrentMedia();
    } catch (error) {
      setFormStatus((prev) => ({ ...prev, error: error.message }));
    }
  };

  const handleSetPrimary = async (mediaId) => {
    if (!selectedId) return;
    try {
      const url = apiBaseUrl
        ? `${apiBaseUrl}/api/admin/products/${selectedId}/media/${mediaId}/primary`
        : `/api/admin/products/${selectedId}/media/${mediaId}/primary`;
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`Set primary failed (${response.status})`);
      }
      await reloadCurrentMedia();
    } catch (error) {
      setFormStatus((prev) => ({ ...prev, error: error.message }));
    }
  };

  const handleCatCreate = async (e) => {
    e.preventDefault();
    setCatCreating(true);
    setCatCreateError(null);
    try {
      const res = await fetch(withBase("/api/admin/categories"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: catNewName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to create category.");
      setCatNewName("");
      await loadCategories();
    } catch (err) {
      setCatCreateError(err.message);
    } finally {
      setCatCreating(false);
    }
  };

  const handleCatUpdate = async (id) => {
    setCatEditError(null);
    try {
      const res = await fetch(withBase(`/api/admin/categories/${id}`), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: catEditName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to rename category.");
      setCatEditingId(null);
      await loadCategories();
      // Refresh the form category value if it changed
      await loadProducts();
    } catch (err) {
      setCatEditError(err.message);
    }
  };

  const handleCatDelete = async (id, name) => {
    if (
      !window.confirm(
        `Delete category "${name}"?\n\nProducts in this category will be reset to "General".`
      )
    )
      return;
    try {
      const res = await fetch(withBase(`/api/admin/categories/${id}`), {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to delete category.");
      }
      await loadCategories();
    } catch (err) {
      alert(err.message);
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

              <div className="row g-3 mt-0">
                <div className="col-12 col-md-6">
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
                <div className="col-12 col-md-6">
                  <label className="form-label">Category</label>
                  <select
                    className="form-select"
                    value={form.category}
                    onChange={(event) =>
                      updateForm("category", event.target.value)
                    }
                  >
                    <option value="general">General (uncategorized)</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.slug}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                  {categories.length === 0 && (
                    <div className="form-text text-muted">
                      <a href="/admin/categories" onClick={(e) => { e.preventDefault(); window.history.pushState({}, "", "/admin/categories"); window.dispatchEvent(new PopStateEvent("popstate")); }}>
                        Create categories
                      </a>{" "}
                      to organize your products.
                    </div>
                  )}
                </div>
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
                {currentMedia.media?.filter((item) => item.type === "image").length ? (
                  <div className="d-flex flex-wrap gap-2 mb-2">
                    {currentMedia.media
                      .filter((item) => item.type === "image")
                      .map((item) => (
                        <div
                          key={item.id}
                          className="position-relative border rounded p-1"
                          style={{ width: "80px" }}
                        >
                          <img
                            src={item.url}
                            alt={item.alt_text || "Gallery"}
                            className="rounded"
                            style={{ width: "64px", height: "64px", objectFit: "cover", display: "block", margin: "0 auto" }}
                          />
                          {item.is_primary ? (
                            <span
                              className="badge bg-success d-block text-center mt-1"
                              style={{ fontSize: "0.65rem" }}
                            >
                              Primary
                            </span>
                          ) : (
                            <button
                              type="button"
                              className="btn btn-outline-secondary btn-sm d-block w-100 mt-1"
                              style={{ fontSize: "0.6rem", padding: "1px 2px" }}
                              onClick={() => handleSetPrimary(item.id)}
                            >
                              Set Primary
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn-danger btn-sm position-absolute top-0 end-0"
                            style={{
                              width: "20px",
                              height: "20px",
                              padding: 0,
                              fontSize: "0.7rem",
                              lineHeight: "20px",
                              borderRadius: "50%",
                            }}
                            onClick={() => handleDeleteMedia(item.id)}
                            title="Remove image"
                          >
                            &times;
                          </button>
                        </div>
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
                        <div key={item.id} className="d-flex align-items-center gap-2">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-truncate"
                          >
                            {item.url}
                          </a>
                          <button
                            type="button"
                            className="btn btn-outline-danger btn-sm"
                            style={{ fontSize: "0.7rem", padding: "1px 6px" }}
                            onClick={() => handleDeleteMedia(item.id)}
                            title="Remove video"
                          >
                            &times;
                          </button>
                        </div>
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

      {/* ── Categories section ── */}
      <div className="mt-5">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <div>
            <h2 className="h5 fw-bold mb-0">Categories</h2>
            <p className="text-muted small mb-0">
              Create and manage categories. They appear as filter tabs in the store.
            </p>
          </div>
        </div>

        <div className="row g-4">
          {/* Quick-create form */}
          <div className="col-12 col-md-4">
            <div className="border rounded bg-white p-4 h-100">
              <h3 className="h6 fw-semibold mb-3">New Category</h3>
              <form onSubmit={handleCatCreate}>
                <div className="mb-3">
                  <label className="form-label">Name</label>
                  <input
                    className="form-control"
                    placeholder="e.g. Apparel, Roles, Digital…"
                    value={catNewName}
                    onChange={(e) => setCatNewName(e.target.value)}
                    required
                  />
                  <div className="form-text text-muted">
                    A URL slug is generated automatically.
                  </div>
                </div>
                {catCreateError && (
                  <div className="alert alert-danger py-2 small">
                    {catCreateError}
                  </div>
                )}
                <button
                  type="submit"
                  className="btn btn-dark btn-sm"
                  disabled={catCreating || !catNewName.trim()}
                >
                  {catCreating ? "Creating…" : "Create Category"}
                </button>
              </form>
            </div>
          </div>

          {/* Category list */}
          <div className="col-12 col-md-8">
            <div className="border rounded bg-white p-4">
              <h3 className="h6 fw-semibold mb-3">
                All Categories{" "}
                <span className="badge bg-light text-dark fw-normal ms-1">
                  {categories.length}
                </span>
              </h3>

              {categories.length === 0 ? (
                <p className="text-muted small mb-0">
                  No categories yet — create one to get started.
                </p>
              ) : (
                <div className="list-group list-group-flush">
                  {categories.map((cat) => (
                    <div
                      key={cat.id}
                      className="list-group-item px-0 d-flex flex-wrap align-items-center gap-2"
                    >
                      {catEditingId === cat.id ? (
                        <>
                          <div className="flex-grow-1">
                            <input
                              className="form-control form-control-sm"
                              value={catEditName}
                              onChange={(e) => setCatEditName(e.target.value)}
                              autoFocus
                            />
                            {catEditError && (
                              <div className="text-danger small mt-1">
                                {catEditError}
                              </div>
                            )}
                          </div>
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => handleCatUpdate(cat.id)}
                            disabled={!catEditName.trim()}
                          >
                            Save
                          </button>
                          <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => setCatEditingId(null)}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <div className="flex-grow-1">
                            <span className="fw-semibold">{cat.name}</span>
                            <span className="text-muted small ms-2">
                              <code>{cat.slug}</code>
                            </span>
                            <span className="badge bg-light text-dark ms-2 fw-normal">
                              {cat.product_count}{" "}
                              {cat.product_count === 1 ? "product" : "products"}
                            </span>
                          </div>
                          <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => {
                              setCatEditingId(cat.id);
                              setCatEditName(cat.name);
                              setCatEditError(null);
                            }}
                          >
                            Rename
                          </button>
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleCatDelete(cat.id, cat.name)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

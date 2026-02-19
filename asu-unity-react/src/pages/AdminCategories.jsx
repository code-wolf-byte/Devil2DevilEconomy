import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function AdminCategories({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [categories, setCategories] = React.useState([]);
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [newName, setNewName] = React.useState("");
  const [creating, setCreating] = React.useState(false);
  const [createError, setCreateError] = React.useState(null);
  const [editingId, setEditingId] = React.useState(null);
  const [editName, setEditName] = React.useState("");
  const [editError, setEditError] = React.useState(null);
  const [assignModal, setAssignModal] = React.useState(null); // { id, name, slug }
  const [assignMode, setAssignMode] = React.useState("uncategorized");
  const [assignStatus, setAssignStatus] = React.useState(null);

  const apiBaseUrl = React.useMemo(buildApiBase, []);
  const withBase = (path) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path);

  const loadCategories = React.useCallback(async () => {
    try {
      setStatus({ loading: true, error: null });
      const res = await fetch(withBase("/api/admin/categories"), {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Failed to load categories (${res.status})`);
      const data = await res.json();
      setCategories(Array.isArray(data.categories) ? data.categories : []);
      setStatus({ loading: false, error: null });
    } catch (err) {
      setStatus({ loading: false, error: err.message });
    }
  }, [apiBaseUrl]);

  React.useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      return;
    }
    loadCategories();
  }, [isAuthenticated, isAdmin, loadCategories]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const res = await fetch(withBase("/api/admin/categories"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to create category.");
      setNewName("");
      await loadCategories();
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (cat) => {
    setEditingId(cat.id);
    setEditName(cat.name);
    setEditError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName("");
    setEditError(null);
  };

  const handleUpdate = async (id) => {
    setEditError(null);
    try {
      const res = await fetch(withBase(`/api/admin/categories/${id}`), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: editName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to update category.");
      setEditingId(null);
      await loadCategories();
    } catch (err) {
      setEditError(err.message);
    }
  };

  const handleDelete = async (id, name) => {
    if (
      !window.confirm(
        `Delete category "${name}"?\n\nProducts in this category will be reset to "general".`
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

  const openAssignModal = (cat) => {
    setAssignModal(cat);
    setAssignMode("uncategorized");
    setAssignStatus(null);
  };

  const handleAssignAll = async () => {
    if (!assignModal) return;
    setAssignStatus({ loading: true, error: null, updated: null });
    try {
      const res = await fetch(
        withBase(`/api/admin/categories/${assignModal.id}/assign-all`),
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uncategorized_only: assignMode === "uncategorized" }),
        }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to assign category.");
      setAssignStatus({ loading: false, error: null, updated: data.updated });
      await loadCategories();
    } catch (err) {
      setAssignStatus({ loading: false, error: err.message, updated: null });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Categories</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Categories</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
          <h1 className="display-6 fw-bold mb-1">Categories</h1>
          <p className="text-muted mb-0">
            Create and manage store product categories. Use "Assign to Products"
            to retroactively apply a category.
          </p>
        </div>
        <Button
          label="Manage Products"
          color="gray"
          href="/admin/products"
          onClick={(e) => {
            e.preventDefault();
            window.history.pushState({}, "", "/admin/products");
            window.dispatchEvent(new PopStateEvent("popstate"));
          }}
        />
      </div>

      {status.error && (
        <div className="alert alert-danger">{status.error}</div>
      )}

      <div className="row g-4">
        {/* Create category form */}
        <div className="col-12 col-lg-4">
          <div className="border rounded bg-white p-4">
            <h2 className="h5 fw-bold mb-3">New Category</h2>
            <form onSubmit={handleCreate}>
              <div className="mb-3">
                <label className="form-label">Category Name</label>
                <input
                  className="form-control"
                  placeholder="e.g. Apparel, Digital, Roles…"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
                <div className="form-text text-muted">
                  A URL slug will be generated automatically.
                </div>
              </div>
              {createError && (
                <div className="alert alert-danger py-2">{createError}</div>
              )}
              <Button
                label={creating ? "Creating…" : "Create Category"}
                color="gold"
                disabled={creating || !newName.trim()}
              />
            </form>
          </div>
        </div>

        {/* Category list */}
        <div className="col-12 col-lg-8">
          <div className="border rounded bg-white p-4">
            <h2 className="h5 fw-bold mb-3">
              All Categories{" "}
              <span className="badge bg-light text-dark fw-normal">
                {categories.length}
              </span>
            </h2>

            {status.loading ? (
              <p className="text-muted">Loading categories…</p>
            ) : categories.length === 0 ? (
              <p className="text-muted">
                No categories yet. Create one to get started.
              </p>
            ) : (
              <div className="list-group">
                {categories.map((cat) => (
                  <div
                    key={cat.id}
                    className="list-group-item d-flex flex-wrap align-items-center gap-3"
                  >
                    {editingId === cat.id ? (
                      <>
                        <div className="flex-grow-1">
                          <input
                            className="form-control form-control-sm"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            autoFocus
                          />
                          {editError && (
                            <div className="text-danger small mt-1">
                              {editError}
                            </div>
                          )}
                        </div>
                        <div className="d-flex gap-2">
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => handleUpdate(cat.id)}
                            disabled={!editName.trim()}
                          >
                            Save
                          </button>
                          <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={cancelEdit}
                          >
                            Cancel
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex-grow-1">
                          <div className="fw-semibold">{cat.name}</div>
                          <div className="small text-muted">
                            slug: <code>{cat.slug}</code> &middot;{" "}
                            <strong>{cat.product_count}</strong>{" "}
                            {cat.product_count === 1 ? "product" : "products"}
                          </div>
                        </div>
                        <div className="d-flex flex-wrap gap-2">
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => openAssignModal(cat)}
                            title="Assign this category to products"
                          >
                            Assign to Products
                          </button>
                          <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => startEdit(cat)}
                          >
                            Rename
                          </button>
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleDelete(cat.id, cat.name)}
                          >
                            Delete
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Assign-all modal */}
      {assignModal && (
        <div
          className="modal d-block"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setAssignModal(null);
          }}
        >
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Assign "{assignModal.name}" to Products
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setAssignModal(null)}
                />
              </div>
              <div className="modal-body">
                <p className="text-muted mb-3">
                  Choose which products should receive this category.
                </p>
                <div className="form-check mb-2">
                  <input
                    className="form-check-input"
                    type="radio"
                    id="modeUncategorized"
                    name="assignMode"
                    value="uncategorized"
                    checked={assignMode === "uncategorized"}
                    onChange={() => setAssignMode("uncategorized")}
                  />
                  <label className="form-check-label" htmlFor="modeUncategorized">
                    <strong>Uncategorized products only</strong>
                    <div className="small text-muted">
                      Assign only to products currently set to "general".
                    </div>
                  </label>
                </div>
                <div className="form-check mb-3">
                  <input
                    className="form-check-input"
                    type="radio"
                    id="modeAll"
                    name="assignMode"
                    value="all"
                    checked={assignMode === "all"}
                    onChange={() => setAssignMode("all")}
                  />
                  <label className="form-check-label" htmlFor="modeAll">
                    <strong>All products (overwrite)</strong>
                    <div className="small text-muted">
                      Overwrite every product's category with this one.
                    </div>
                  </label>
                </div>

                {assignStatus?.error && (
                  <div className="alert alert-danger py-2">
                    {assignStatus.error}
                  </div>
                )}
                {assignStatus?.updated != null && !assignStatus.error && (
                  <div className="alert alert-success py-2">
                    Updated <strong>{assignStatus.updated}</strong>{" "}
                    {assignStatus.updated === 1 ? "product" : "products"}.
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => setAssignModal(null)}
                >
                  Close
                </button>
                <button
                  className="btn btn-warning fw-semibold"
                  onClick={handleAssignAll}
                  disabled={assignStatus?.loading}
                >
                  {assignStatus?.loading ? "Assigning…" : "Assign Now"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

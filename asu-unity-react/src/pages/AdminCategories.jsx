import React from "react";
import {
  ArrowLeft,
  Plus,
  Pencil,
  Trash2,
  Check,
  X,
  Tag,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiUrl } from "@/utils/api";

function LoadingSkeleton() {
  return (
    <div className="container py-5 space-y-6">
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Skeleton className="h-48" />
        <div className="lg:col-span-2 space-y-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
        </div>
      </div>
    </div>
  );
}

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
  const [assignModal, setAssignModal] = React.useState(null);
  const [assignMode, setAssignMode] = React.useState("uncategorized");
  const [assignStatus, setAssignStatus] = React.useState(null);

  const url = useApiUrl();

  const loadCategories = React.useCallback(async () => {
    try {
      setStatus({ loading: true, error: null });
      const res = await fetch(url("/api/admin/categories"), { credentials: "include" });
      if (!res.ok) throw new Error(`Failed to load categories (${res.status})`);
      const data = await res.json();
      setCategories(Array.isArray(data.categories) ? data.categories : []);
      setStatus({ loading: false, error: null });
    } catch (err) {
      setStatus({ loading: false, error: err.message });
    }
  }, [url]);

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
      const res = await fetch(url("/api/admin/categories"), {
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

  const startEdit = (cat) => { setEditingId(cat.id); setEditName(cat.name); setEditError(null); };
  const cancelEdit = () => { setEditingId(null); setEditName(""); setEditError(null); };

  const handleUpdate = async (id) => {
    setEditError(null);
    try {
      const res = await fetch(url(`/api/admin/categories/${id}`), {
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
    if (!window.confirm(`Delete category "${name}"?\n\nProducts in this category will be reset to "general".`)) return;
    try {
      const res = await fetch(url(`/api/admin/categories/${id}`), { method: "DELETE", credentials: "include" });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to delete category.");
      }
      await loadCategories();
    } catch (err) {
      alert(err.message);
    }
  };

  const openAssignModal = (cat) => { setAssignModal(cat); setAssignMode("uncategorized"); setAssignStatus(null); };

  const handleAssignAll = async () => {
    if (!assignModal) return;
    setAssignStatus({ loading: true, error: null, updated: null });
    try {
      const res = await fetch(url(`/api/admin/categories/${assignModal.id}/assign-all`), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uncategorized_only: assignMode === "uncategorized" }),
      });
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
        <p className="text-gray-500 mb-4">Please sign in to access this page.</p>
        <a href={loginHref} className="btn btn-warning">Sign in with Discord</a>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Categories</h1>
        <p className="text-red-600 mb-4">You do not have permission to view this page.</p>
      </div>
    );
  }

  if (status.loading) return <LoadingSkeleton />;

  return (
    <div className="container py-5 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <p className="text-sm text-gray-500 mt-1">
            Create and manage store product categories. Use &ldquo;Assign to Products&rdquo; to retroactively apply a category.
          </p>
        </div>
        <a href="/admin/products">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4" /> Manage Products
          </Button>
        </a>
      </div>

      {status.error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 flex items-center justify-between">
            <span className="text-red-700 text-sm">{status.error}</span>
            <Button size="sm" variant="outline" onClick={loadCategories}>
              <RefreshCw className="h-4 w-4" /> Retry
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create form */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Plus className="h-4 w-4" /> New Category
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Category Name</label>
                <input
                  className="form-control"
                  placeholder="e.g. Apparel, Digital, Roles…"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
                <p className="text-xs text-gray-400 mt-1">A URL slug will be generated automatically.</p>
              </div>
              {createError && (
                <div className="text-sm text-red-600 bg-red-50 rounded p-2">{createError}</div>
              )}
              <Button
                type="submit"
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-white"
                disabled={creating || !newName.trim()}
              >
                <Plus className="h-4 w-4" />
                {creating ? "Creating…" : "Create Category"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Category list */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Tag className="h-4 w-4" />
                All Categories
                <Badge variant="secondary">{categories.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {categories.length === 0 ? (
                <div className="text-center py-10">
                  <Tag className="h-8 w-8 text-gray-200 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">No categories yet. Create one to get started.</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y rounded-lg border overflow-hidden">
                  {categories.map((cat) => (
                    <div key={cat.id} className="flex flex-wrap items-center gap-3 p-3 bg-white">
                      {editingId === cat.id ? (
                        <>
                          <div className="flex-1 min-w-0">
                            <input
                              className="form-control form-control-sm"
                              value={editName}
                              onChange={(e) => setEditName(e.target.value)}
                              autoFocus
                            />
                            {editError && <p className="text-xs text-red-600 mt-1">{editError}</p>}
                          </div>
                          <div className="flex gap-2 shrink-0">
                            <Button
                              size="sm"
                              className="bg-green-600 hover:bg-green-700 text-white"
                              onClick={() => handleUpdate(cat.id)}
                              disabled={!editName.trim()}
                            >
                              <Check className="h-3.5 w-3.5" /> Save
                            </Button>
                            <Button size="sm" variant="outline" onClick={cancelEdit}>
                              <X className="h-3.5 w-3.5" /> Cancel
                            </Button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-sm text-gray-900 truncate">{cat.name}</p>
                            <p className="text-xs text-gray-400">
                              slug: <code className="bg-gray-100 px-1 rounded">{cat.slug}</code>
                              {" · "}
                              <strong>{cat.product_count}</strong>{" "}
                              {cat.product_count === 1 ? "product" : "products"}
                            </p>
                          </div>
                          <div className="flex flex-wrap gap-2 shrink-0">
                            <Button size="sm" variant="outline" onClick={() => openAssignModal(cat)}>
                              Assign to Products
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => startEdit(cat)}>
                              <Pencil className="h-3.5 w-3.5" /> Rename
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 border-red-300 hover:bg-red-50"
                              onClick={() => handleDelete(cat.id, cat.name)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Assign-all modal (keep Bootstrap modal — complex form interaction) */}
      {assignModal && (
        <div
          className="modal d-block"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={(e) => { if (e.target === e.currentTarget) setAssignModal(null); }}
        >
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Assign &ldquo;{assignModal.name}&rdquo; to Products</h5>
                <button type="button" className="btn-close" onClick={() => setAssignModal(null)} />
              </div>
              <div className="modal-body">
                <p className="text-muted mb-3">Choose which products should receive this category.</p>
                <div className="form-check mb-2">
                  <input
                    className="form-check-input" type="radio" id="modeUncategorized" name="assignMode"
                    value="uncategorized" checked={assignMode === "uncategorized"}
                    onChange={() => setAssignMode("uncategorized")}
                  />
                  <label className="form-check-label" htmlFor="modeUncategorized">
                    <strong>Uncategorized products only</strong>
                    <div className="small text-muted">Assign only to products currently set to &ldquo;general&rdquo;.</div>
                  </label>
                </div>
                <div className="form-check mb-3">
                  <input
                    className="form-check-input" type="radio" id="modeAll" name="assignMode"
                    value="all" checked={assignMode === "all"}
                    onChange={() => setAssignMode("all")}
                  />
                  <label className="form-check-label" htmlFor="modeAll">
                    <strong>All products (overwrite)</strong>
                    <div className="small text-muted">Overwrite every product&apos;s category with this one.</div>
                  </label>
                </div>
                {assignStatus?.error && (
                  <div className="alert alert-danger py-2">{assignStatus.error}</div>
                )}
                {assignStatus?.updated != null && !assignStatus.error && (
                  <div className="alert alert-success py-2">
                    Updated <strong>{assignStatus.updated}</strong>{" "}
                    {assignStatus.updated === 1 ? "product" : "products"}.
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-outline-secondary" onClick={() => setAssignModal(null)}>Close</button>
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

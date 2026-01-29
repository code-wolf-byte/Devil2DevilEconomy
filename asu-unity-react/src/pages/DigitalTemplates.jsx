import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function DigitalTemplates({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [activeTab, setActiveTab] = React.useState("discord-roles");
  const [discordRoles, setDiscordRoles] = React.useState([]);
  const [roleProducts, setRoleProducts] = React.useState([]);
  const [skinProducts, setSkinProducts] = React.useState([]);
  const [rolesStatus, setRolesStatus] = React.useState({ loading: true, error: null });
  const [roleProductsStatus, setRoleProductsStatus] = React.useState({ loading: true, error: null });
  const [skinProductsStatus, setSkinProductsStatus] = React.useState({ loading: true, error: null });
  const [roleFormStatus, setRoleFormStatus] = React.useState({ saving: false, error: null, success: null });
  const [skinFormStatus, setSkinFormStatus] = React.useState({ saving: false, error: null, success: null });

  const [roleForm, setRoleForm] = React.useState({
    role_id: "",
    product_name: "",
    description: "",
    price: "",
    stock: "",
    role_image: null,
  });

  const [skinForm, setSkinForm] = React.useState({
    name: "",
    description: "",
    price: "",
    stock: "",
    preview_image: null,
    download_file: null,
  });

  const [selectedRole, setSelectedRole] = React.useState(null);
  const [roleDropdownOpen, setRoleDropdownOpen] = React.useState(false);
  const [roleSearchTerm, setRoleSearchTerm] = React.useState("");

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const loadDiscordRoles = React.useCallback(async () => {
    try {
      setRolesStatus({ loading: true, error: null });
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/discord-roles` : "/api/admin/discord-roles";
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to load Discord roles (${response.status})`);
      }

      const data = await response.json();
      setDiscordRoles(Array.isArray(data.roles) ? data.roles : []);
      setRolesStatus({ loading: false, error: null });
    } catch (error) {
      setRolesStatus({ loading: false, error: error.message });
    }
  }, [apiBaseUrl]);

  const loadRoleProducts = React.useCallback(async () => {
    try {
      setRoleProductsStatus({ loading: true, error: null });
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/digital-templates/roles` : "/api/admin/digital-templates/roles";
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        throw new Error(`Failed to load role products (${response.status})`);
      }

      const data = await response.json();
      setRoleProducts(Array.isArray(data.products) ? data.products : []);
      setRoleProductsStatus({ loading: false, error: null });
    } catch (error) {
      setRoleProductsStatus({ loading: false, error: error.message });
    }
  }, [apiBaseUrl]);

  const loadSkinProducts = React.useCallback(async () => {
    try {
      setSkinProductsStatus({ loading: true, error: null });
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/digital-templates/minecraft-skins` : "/api/admin/digital-templates/minecraft-skins";
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        throw new Error(`Failed to load skin products (${response.status})`);
      }

      const data = await response.json();
      setSkinProducts(Array.isArray(data.products) ? data.products : []);
      setSkinProductsStatus({ loading: false, error: null });
    } catch (error) {
      setSkinProductsStatus({ loading: false, error: error.message });
    }
  }, [apiBaseUrl]);

  React.useEffect(() => {
    if (!isAuthenticated || !isAdmin) return;
    loadDiscordRoles();
    loadRoleProducts();
    loadSkinProducts();
  }, [isAuthenticated, isAdmin, loadDiscordRoles, loadRoleProducts, loadSkinProducts]);

  const handleSelectRole = (role) => {
    setSelectedRole(role);
    setRoleForm((prev) => ({
      ...prev,
      role_id: role.id,
      product_name: prev.product_name || role.name,
    }));
    setRoleDropdownOpen(false);
    setRoleSearchTerm("");
  };

  const filteredRoles = discordRoles.filter((role) =>
    role.name.toLowerCase().includes(roleSearchTerm.toLowerCase())
  );

  const handleRoleFormSubmit = async (event) => {
    event.preventDefault();
    setRoleFormStatus({ saving: true, error: null, success: null });

    try {
      const formData = new FormData();
      formData.append("role_id", roleForm.role_id);
      formData.append("product_name", roleForm.product_name);
      formData.append("description", roleForm.description);
      formData.append("price", roleForm.price);
      formData.append("stock", roleForm.stock);
      if (roleForm.role_image) {
        formData.append("role_image", roleForm.role_image);
      }

      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/digital-templates/roles` : "/api/admin/digital-templates/roles";
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to create role product (${response.status})`);
      }

      setRoleFormStatus({ saving: false, error: null, success: "Role product created successfully!" });
      setRoleForm({ role_id: "", product_name: "", description: "", price: "", stock: "", role_image: null });
      setSelectedRole(null);
      await loadRoleProducts();
    } catch (error) {
      setRoleFormStatus({ saving: false, error: error.message, success: null });
    }
  };

  const handleSkinFormSubmit = async (event) => {
    event.preventDefault();
    setSkinFormStatus({ saving: true, error: null, success: null });

    try {
      const formData = new FormData();
      formData.append("name", skinForm.name);
      formData.append("description", skinForm.description);
      formData.append("price", skinForm.price);
      formData.append("stock", skinForm.stock);
      if (skinForm.preview_image) {
        formData.append("preview_image", skinForm.preview_image);
      }
      if (skinForm.download_file) {
        formData.append("download_file", skinForm.download_file);
      }

      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/digital-templates/minecraft-skins` : "/api/admin/digital-templates/minecraft-skins";
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to create skin product (${response.status})`);
      }

      setSkinFormStatus({ saving: false, error: null, success: "Minecraft skin product created successfully!" });
      setSkinForm({ name: "", description: "", price: "", stock: "", preview_image: null, download_file: null });
      await loadSkinProducts();
    } catch (error) {
      setSkinFormStatus({ saving: false, error: error.message, success: null });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Digital Product Creator</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Digital Product Creator</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
        <Button label="Back to Dashboard" color="gray" href="/dashboard" />
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="text-center mb-4">
        <h1 className="display-6 fw-bold mb-2">Digital Product Creator</h1>
        <p className="text-muted">Create digital products that deliver automatically to your customers</p>
      </div>

      <div className="border rounded bg-white p-4 mb-4 text-center">
        <div className="display-4 text-primary mb-3">&#x2139;</div>
        <h3 className="h5 fw-semibold mb-3">How Digital Products Work</h3>
        <p className="text-muted">
          Digital products are automatically delivered to users after purchase.
          Discord roles are assigned instantly, files are made available for download,
          and codes are generated automatically.
        </p>
      </div>

      <div className="border rounded bg-white mb-4">
        <div className="d-flex border-bottom">
          <button
            type="button"
            className={`flex-grow-1 py-3 px-4 border-0 bg-transparent fw-medium ${
              activeTab === "discord-roles"
                ? "border-bottom border-warning border-3 text-warning"
                : "text-muted"
            }`}
            onClick={() => setActiveTab("discord-roles")}
          >
            <span className="text-purple me-2">&#128100;</span>
            Discord Roles
          </button>
          <button
            type="button"
            className={`flex-grow-1 py-3 px-4 border-0 bg-transparent fw-medium ${
              activeTab === "minecraft-skins"
                ? "border-bottom border-warning border-3 text-warning"
                : "text-muted"
            }`}
            onClick={() => setActiveTab("minecraft-skins")}
          >
            <span className="text-success me-2">&#128230;</span>
            Minecraft Skins
          </button>
        </div>
      </div>

      {activeTab === "discord-roles" && (
        <div className="border rounded bg-white p-4 mb-4">
          <div className="text-center mb-4">
            <div className="display-4 text-purple mb-3">&#128100;</div>
            <h2 className="h4 fw-bold mb-2">Discord Role Products</h2>
            <p className="text-muted">Create purchasable products that automatically assign Discord roles to users</p>
          </div>

          {rolesStatus.loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary mb-3" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="text-muted">Loading Discord roles...</p>
            </div>
          ) : rolesStatus.error ? (
            <div className="alert alert-danger">
              <strong>Failed to load Discord roles</strong>
              <p className="mb-2">{rolesStatus.error}</p>
              <Button label="Retry" color="gold" onClick={loadDiscordRoles} />
            </div>
          ) : (
            <>
              <div className="border rounded p-4 mb-4" style={{ background: "linear-gradient(to right, rgba(102, 51, 153, 0.1), rgba(255, 105, 180, 0.1))" }}>
                <h3 className="h5 fw-bold mb-4 text-center">Create Role Product</h3>

                <form onSubmit={handleRoleFormSubmit}>
                  <div className="row g-3">
                    <div className="col-12 col-lg-6">
                      <label className="form-label">Select Discord Role *</label>
                      <div className="position-relative">
                        <div
                          className="form-control d-flex align-items-center justify-content-between"
                          style={{ cursor: "pointer" }}
                          onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
                        >
                          {selectedRole ? (
                            <div className="d-flex align-items-center gap-2">
                              <span
                                className="rounded-circle"
                                style={{
                                  width: "12px",
                                  height: "12px",
                                  backgroundColor: selectedRole.color || "#ffffff",
                                }}
                              />
                              <span>{selectedRole.name}</span>
                            </div>
                          ) : (
                            <span className="text-muted">Choose a role...</span>
                          )}
                          <span>&#x25BC;</span>
                        </div>

                        {roleDropdownOpen && (
                          <div className="position-absolute top-100 start-0 end-0 bg-white border rounded shadow-lg mt-1 z-3">
                            <div className="p-2 border-bottom">
                              <input
                                type="text"
                                className="form-control form-control-sm"
                                placeholder="Search roles..."
                                value={roleSearchTerm}
                                onChange={(e) => setRoleSearchTerm(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                              />
                            </div>
                            <div style={{ maxHeight: "200px", overflowY: "auto" }}>
                              {filteredRoles.length === 0 ? (
                                <div className="p-3 text-center text-muted">No roles found</div>
                              ) : (
                                filteredRoles.map((role) => (
                                  <div
                                    key={role.id}
                                    className="d-flex align-items-center gap-2 p-2 hover-bg-light"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => handleSelectRole(role)}
                                  >
                                    <span
                                      className="rounded-circle"
                                      style={{
                                        width: "12px",
                                        height: "12px",
                                        backgroundColor: role.color || "#ffffff",
                                      }}
                                    />
                                    <span className="flex-grow-1">{role.name}</span>
                                    <span className="text-muted small">#{role.position}</span>
                                  </div>
                                ))
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      <small className="text-muted">Only roles that can be managed by the bot are shown</small>
                    </div>

                    <div className="col-12 col-lg-6">
                      <label className="form-label">Product Name *</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="e.g., VIP Member Access"
                        value={roleForm.product_name}
                        onChange={(e) => setRoleForm((prev) => ({ ...prev, product_name: e.target.value }))}
                        required
                      />
                    </div>

                    <div className="col-12 col-lg-6">
                      <label className="form-label">Description</label>
                      <textarea
                        className="form-control"
                        rows="3"
                        placeholder="Describe what this role provides..."
                        value={roleForm.description}
                        onChange={(e) => setRoleForm((prev) => ({ ...prev, description: e.target.value }))}
                      />
                      <small className="text-muted">Leave empty for auto-generated description</small>
                    </div>

                    <div className="col-12 col-lg-6">
                      <label className="form-label">Price (Pitchforks) *</label>
                      <input
                        type="number"
                        className="form-control"
                        placeholder="100"
                        min="1"
                        value={roleForm.price}
                        onChange={(e) => setRoleForm((prev) => ({ ...prev, price: e.target.value }))}
                        required
                      />
                    </div>

                    <div className="col-12 col-lg-6">
                      <label className="form-label">Stock Quantity</label>
                      <input
                        type="number"
                        className="form-control"
                        placeholder="Leave empty for unlimited"
                        min="1"
                        value={roleForm.stock}
                        onChange={(e) => setRoleForm((prev) => ({ ...prev, stock: e.target.value }))}
                      />
                      <small className="text-muted">Leave empty for unlimited stock</small>
                    </div>

                    <div className="col-12 col-lg-6">
                      <label className="form-label">Role Image (Optional)</label>
                      <input
                        type="file"
                        className="form-control"
                        accept="image/*"
                        onChange={(e) => setRoleForm((prev) => ({ ...prev, role_image: e.target.files?.[0] || null }))}
                      />
                    </div>
                  </div>

                  {roleFormStatus.error && (
                    <div className="alert alert-danger mt-3">{roleFormStatus.error}</div>
                  )}
                  {roleFormStatus.success && (
                    <div className="alert alert-success mt-3">{roleFormStatus.success}</div>
                  )}

                  <div className="text-center mt-4">
                    <Button
                      label={roleFormStatus.saving ? "Creating..." : "Create Role Product"}
                      color="gold"
                      disabled={roleFormStatus.saving || !roleForm.role_id || !roleForm.product_name || !roleForm.price}
                    />
                  </div>
                </form>
              </div>

              {roleProductsStatus.loading ? (
                <div className="text-center py-4">
                  <div className="spinner-border spinner-border-sm text-muted" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                </div>
              ) : roleProducts.length > 0 && (
                <div className="border-top pt-4">
                  <h3 className="h5 fw-bold mb-3 text-center">Existing Role Products</h3>
                  <div className="row g-3">
                    {roleProducts.map((product) => (
                      <div key={product.id} className="col-12 col-md-6 col-lg-4">
                        <div className="border rounded bg-light p-3 h-100">
                          {product.image_url ? (
                            <img
                              src={product.image_url}
                              alt={product.name}
                              className="rounded mb-3 w-100"
                              style={{ height: "120px", objectFit: "cover" }}
                            />
                          ) : (
                            <div className="rounded mb-3 bg-secondary d-flex align-items-center justify-content-center text-white" style={{ height: "120px" }}>
                              &#128100;
                            </div>
                          )}
                          <h4 className="h6 fw-semibold mb-1">{product.name}</h4>
                          <p className="small text-muted mb-2">{product.description || "No description"}</p>
                          <div className="d-flex align-items-center justify-content-between mb-2">
                            <span className="fw-bold text-warning">{product.price} pts</span>
                            <span className="small text-muted">
                              Stock: {product.stock === null ? "Unlimited" : product.stock === 0 ? "Out" : product.stock}
                            </span>
                          </div>
                          <a href={`/admin/products/${product.id}`} className="btn btn-sm btn-outline-primary w-100">
                            Edit Product
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === "minecraft-skins" && (
        <div className="border rounded bg-white p-4 mb-4">
          <div className="text-center mb-4">
            <div className="display-4 text-success mb-3">&#128230;</div>
            <h2 className="h4 fw-bold mb-2">Minecraft Skin Products</h2>
            <p className="text-muted">Create downloadable Minecraft skin products with instant file delivery</p>
          </div>

          {skinProductsStatus.loading ? (
            <div className="text-center py-4">
              <div className="spinner-border spinner-border-sm text-muted" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          ) : skinProducts.length > 0 && (
            <div className="mb-4">
              <h3 className="h5 fw-bold mb-3 text-center">Existing Minecraft Skin Products</h3>
              <div className="row g-3">
                {skinProducts.map((product) => (
                  <div key={product.id} className="col-12 col-md-6 col-lg-4">
                    <div className="border rounded bg-light p-3 h-100">
                      {product.preview_image_url ? (
                        product.preview_type === "video" ? (
                          <video
                            src={product.preview_image_url}
                            className="rounded mb-3 w-100"
                            style={{ height: "120px", objectFit: "cover" }}
                            muted
                            loop
                            autoPlay
                            playsInline
                          />
                        ) : (
                          <img
                            src={product.preview_image_url}
                            alt={product.name}
                            className="rounded mb-3 w-100"
                            style={{ height: "120px", objectFit: "cover" }}
                          />
                        )
                      ) : (
                        <div className="rounded mb-3 bg-secondary d-flex align-items-center justify-content-center text-white" style={{ height: "120px" }}>
                          &#128230;
                        </div>
                      )}
                      <h4 className="h6 fw-semibold mb-1">{product.name}</h4>
                      <p className="small text-muted mb-2">{product.description || "No description"}</p>
                      <div className="d-flex align-items-center justify-content-between mb-2">
                        <span className="fw-bold text-warning">{product.price} pts</span>
                        <span className="small text-muted">
                          Stock: {product.stock === null ? "Unlimited" : product.stock === 0 ? "Out" : product.stock}
                        </span>
                      </div>
                      <div className="d-flex flex-wrap gap-1 mb-2">
                        {product.has_dual_files && (
                          <span className="badge bg-success">Dual-file</span>
                        )}
                        {product.download_file_url && (
                          <span className="badge bg-primary">Download</span>
                        )}
                      </div>
                      <a href={`/admin/products/${product.id}`} className="btn btn-sm btn-outline-primary w-100">
                        Edit Product
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border rounded p-4" style={{ background: "linear-gradient(to right, rgba(0, 123, 255, 0.1), rgba(0, 255, 255, 0.1))" }}>
            <h3 className="h5 fw-bold mb-4 text-center">Create New Minecraft Skin Product</h3>
            <p className="text-muted text-center mb-4">
              Create a new Minecraft skin product with preview media and downloadable files.
            </p>

            <form onSubmit={handleSkinFormSubmit}>
              <div className="row g-3">
                <div className="col-12 col-lg-6">
                  <label className="form-label">Product Name *</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g., Epic Knight Skin"
                    value={skinForm.name}
                    onChange={(e) => setSkinForm((prev) => ({ ...prev, name: e.target.value }))}
                    required
                  />
                </div>

                <div className="col-12 col-lg-6">
                  <label className="form-label">Price (Pitchforks) *</label>
                  <input
                    type="number"
                    className="form-control"
                    placeholder="150"
                    min="1"
                    value={skinForm.price}
                    onChange={(e) => setSkinForm((prev) => ({ ...prev, price: e.target.value }))}
                    required
                  />
                </div>

                <div className="col-12">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    placeholder="Describe your skin..."
                    value={skinForm.description}
                    onChange={(e) => setSkinForm((prev) => ({ ...prev, description: e.target.value }))}
                  />
                </div>

                <div className="col-12 col-lg-6">
                  <label className="form-label">Preview Media (Image or Video) *</label>
                  <input
                    type="file"
                    className="form-control"
                    accept="image/*,video/*"
                    onChange={(e) => setSkinForm((prev) => ({ ...prev, preview_image: e.target.files?.[0] || null }))}
                    required
                  />
                  <small className="text-muted">This will be shown to customers as a preview of the skin</small>
                </div>

                <div className="col-12 col-lg-6">
                  <label className="form-label">Downloadable Skin File *</label>
                  <input
                    type="file"
                    className="form-control"
                    accept=".png,.zip,.rar,.7z,.mcpack,.mcworld,.mctemplate,.mcaddon"
                    onChange={(e) => setSkinForm((prev) => ({ ...prev, download_file: e.target.files?.[0] || null }))}
                    required
                  />
                  <small className="text-muted">This file will be downloaded by customers after purchase</small>
                </div>

                <div className="col-12 col-lg-6">
                  <label className="form-label">Stock Quantity</label>
                  <input
                    type="number"
                    className="form-control"
                    placeholder="Leave empty for unlimited"
                    min="1"
                    value={skinForm.stock}
                    onChange={(e) => setSkinForm((prev) => ({ ...prev, stock: e.target.value }))}
                  />
                </div>
              </div>

              {skinFormStatus.error && (
                <div className="alert alert-danger mt-3">{skinFormStatus.error}</div>
              )}
              {skinFormStatus.success && (
                <div className="alert alert-success mt-3">{skinFormStatus.success}</div>
              )}

              <div className="text-center mt-4">
                <Button
                  label={skinFormStatus.saving ? "Creating..." : "Create Skin Product"}
                  color="gold"
                  disabled={skinFormStatus.saving || !skinForm.name || !skinForm.price}
                />
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="text-center d-flex flex-wrap gap-3 justify-content-center">
        <Button label="Back to Admin Panel" color="gray" href="/dashboard" />
        <Button label="Advanced Product Creator" color="gold" href="/admin/products/new" />
      </div>
    </div>
  );
}

import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

export default function EconomyConfig({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [roles, setRoles] = React.useState([]);
  const [settings, setSettings] = React.useState({
    economy_enabled: false,
    verified_role_id: null,
    verified_bonus_points: 200,
    onboarding_role_ids: [],
    onboarding_bonus_points: 500,
    roles_configured: false,
  });
  const [selectedOnboardingRoles, setSelectedOnboardingRoles] = React.useState([]);
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [saveStatus, setSaveStatus] = React.useState({ saving: false, error: null, success: null });

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const loadData = React.useCallback(async () => {
    try {
      setStatus({ loading: true, error: null });

      const rolesUrl = apiBaseUrl ? `${apiBaseUrl}/api/admin/discord-roles` : "/api/admin/discord-roles";
      const configUrl = apiBaseUrl ? `${apiBaseUrl}/api/admin/economy-config` : "/api/admin/economy-config";

      const [rolesRes, configRes] = await Promise.all([
        fetch(rolesUrl, { credentials: "include" }),
        fetch(configUrl, { credentials: "include" }),
      ]);

      if (!rolesRes.ok) {
        const errorData = await rolesRes.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to load Discord roles (${rolesRes.status})`);
      }
      if (!configRes.ok) {
        throw new Error(`Failed to load economy config (${configRes.status})`);
      }

      const rolesData = await rolesRes.json();
      const configData = await configRes.json();

      setRoles(Array.isArray(rolesData.roles) ? rolesData.roles : []);
      if (configData.settings) {
        setSettings(configData.settings);
        setSelectedOnboardingRoles(configData.settings.onboarding_role_ids || []);
      }
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
    loadData();
  }, [isAuthenticated, isAdmin, loadData]);

  const handleVerifiedRoleChange = (event) => {
    setSettings((prev) => ({ ...prev, verified_role_id: event.target.value || null }));
  };

  const handleVerifiedPointsChange = (event) => {
    setSettings((prev) => ({ ...prev, verified_bonus_points: parseInt(event.target.value, 10) || 0 }));
  };

  const handleOnboardingPointsChange = (event) => {
    setSettings((prev) => ({ ...prev, onboarding_bonus_points: parseInt(event.target.value, 10) || 0 }));
  };

  const toggleOnboardingRole = (roleId) => {
    setSelectedOnboardingRoles((prev) => {
      if (prev.includes(roleId)) {
        return prev.filter((id) => id !== roleId);
      }
      return [...prev, roleId];
    });
  };

  const handleSave = async (action = "save_config") => {
    setSaveStatus({ saving: true, error: null, success: null });

    try {
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/economy-config` : "/api/admin/economy-config";
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          action,
          verified_role_id: settings.verified_role_id,
          verified_bonus_points: settings.verified_bonus_points,
          onboarding_role_ids: selectedOnboardingRoles,
          onboarding_bonus_points: settings.onboarding_bonus_points,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Save failed (${response.status})`);
      }

      const successMessage = action === "enable_economy"
        ? "Economy system enabled successfully!"
        : "Configuration saved successfully!";
      setSaveStatus({ saving: false, error: null, success: successMessage });

      await loadData();
    } catch (error) {
      setSaveStatus({ saving: false, error: error.message, success: null });
    }
  };

  const getSelectedVerifiedRole = () => {
    if (!settings.verified_role_id) return null;
    return roles.find((r) => r.id === settings.verified_role_id);
  };

  const canEnableEconomy = settings.verified_role_id || selectedOnboardingRoles.length > 0;

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Configuration</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Configuration</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
        <Button label="Back to Dashboard" color="gray" href="/dashboard" />
      </div>
    );
  }

  if (status.loading) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Configuration</h1>
        <div className="border rounded bg-white p-5 text-center">
          <div className="spinner-border text-warning mb-3" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted mb-0">Loading Discord roles...</p>
        </div>
      </div>
    );
  }

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Configuration</h1>
        <div className="alert alert-danger">
          <strong>Failed to Load Discord Roles</strong>
          <p className="mb-0">{status.error}</p>
        </div>
        <Button label="Retry" color="gold" onClick={loadData} />
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="text-center mb-4">
        <h1 className="display-6 fw-bold mb-2">Economy System Configuration</h1>
        <p className="text-muted">
          Configure roles and bonuses before enabling the economy system for the first time
        </p>
      </div>

      <div className="alert alert-warning mb-4">
        <strong>Important Configuration</strong>
        <p className="mb-0">
          Configure these settings before enabling the economy system for the first time.
          Users with the selected roles will automatically receive bonus points when the economy is enabled.
        </p>
      </div>

      <div className="border rounded bg-white p-4 mb-4">
        <h2 className="h5 fw-bold mb-3 d-flex align-items-center gap-2">
          <span className="text-success">Verified Role Configuration</span>
        </h2>
        <p className="text-muted small mb-3">
          Select the Discord role that represents verified members.
          Users with this role will receive bonus points when the economy is first enabled.
        </p>

        <div className="row g-3">
          <div className="col-12 col-lg-8">
            <label className="form-label">Select Verified Role</label>
            <select
              className="form-select"
              value={settings.verified_role_id || ""}
              onChange={handleVerifiedRoleChange}
            >
              <option value="">Select a role...</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
          </div>
          <div className="col-12 col-lg-4">
            <label className="form-label">Bonus Points</label>
            <input
              type="number"
              className="form-control"
              value={settings.verified_bonus_points}
              onChange={handleVerifiedPointsChange}
              min="0"
              max="10000"
            />
          </div>
        </div>
      </div>

      <div className="border rounded bg-white p-4 mb-4">
        <h2 className="h5 fw-bold mb-3 d-flex align-items-center gap-2">
          <span className="text-primary">Onboarding Roles Configuration</span>
        </h2>
        <p className="text-muted small mb-3">
          Select Discord roles that represent users who completed onboarding.
          Users with any of these roles will receive bonus points when the economy is first enabled.
        </p>

        <div className="row g-3">
          <div className="col-12 col-lg-8">
            <label className="form-label">Select Onboarding Roles (Multiple Allowed)</label>
            <div
              className="border rounded p-3"
              style={{ maxHeight: "300px", overflowY: "auto" }}
            >
              {roles.length === 0 ? (
                <p className="text-muted mb-0">No roles available</p>
              ) : (
                roles.map((role) => (
                  <div
                    key={role.id}
                    className={`d-flex align-items-center justify-content-between p-2 rounded mb-2 ${
                      selectedOnboardingRoles.includes(role.id)
                        ? "bg-warning bg-opacity-25 border border-warning"
                        : "bg-light"
                    }`}
                    style={{ cursor: "pointer" }}
                    onClick={() => toggleOnboardingRole(role.id)}
                  >
                    <div className="d-flex align-items-center gap-2">
                      <span
                        className="rounded-circle"
                        style={{
                          width: "12px",
                          height: "12px",
                          backgroundColor: role.color || "#ffffff",
                        }}
                      />
                      <span className="fw-medium">{role.name}</span>
                      <span className="text-muted small">Position: {role.position}</span>
                    </div>
                    <input
                      type="checkbox"
                      className="form-check-input"
                      checked={selectedOnboardingRoles.includes(role.id)}
                      onChange={() => toggleOnboardingRole(role.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                ))
              )}
            </div>
          </div>
          <div className="col-12 col-lg-4">
            <label className="form-label">Bonus Points</label>
            <input
              type="number"
              className="form-control"
              value={settings.onboarding_bonus_points}
              onChange={handleOnboardingPointsChange}
              min="0"
              max="10000"
            />
          </div>
        </div>
      </div>

      <div className="border rounded bg-white p-4 mb-4">
        <h2 className="h5 fw-bold mb-3">Configuration Preview</h2>
        <div className="bg-light rounded p-3">
          {settings.verified_role_id ? (
            <div className="d-flex align-items-center justify-content-between p-2 mb-2 rounded bg-success bg-opacity-10 border border-success">
              <div className="d-flex align-items-center gap-2">
                <span className="fw-medium">Verified Role:</span>
                <span className="badge bg-success">{getSelectedVerifiedRole()?.name || "Unknown"}</span>
              </div>
              <span className="text-warning fw-bold">{settings.verified_bonus_points} points</span>
            </div>
          ) : (
            <div className="p-2 mb-2 rounded bg-light text-muted">No verified role selected</div>
          )}

          {selectedOnboardingRoles.length > 0 ? (
            <div className="p-2 rounded bg-primary bg-opacity-10 border border-primary">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <span className="fw-medium">Onboarding Roles:</span>
                <span className="text-warning fw-bold">{settings.onboarding_bonus_points} points each</span>
              </div>
              <div className="d-flex flex-wrap gap-2">
                {selectedOnboardingRoles.map((roleId) => {
                  const role = roles.find((r) => r.id === roleId);
                  return role ? (
                    <span key={roleId} className="badge bg-primary">{role.name}</span>
                  ) : null;
                })}
              </div>
            </div>
          ) : (
            <div className="p-2 rounded bg-light text-muted">No onboarding roles selected</div>
          )}

          <p className="text-muted small mt-3 mb-0">
            When the economy is enabled, users with these roles will automatically receive the configured bonus points.
          </p>
        </div>
      </div>

      {saveStatus.error && (
        <div className="alert alert-danger">{saveStatus.error}</div>
      )}
      {saveStatus.success && (
        <div className="alert alert-success">{saveStatus.success}</div>
      )}

      <div className="border rounded bg-white p-4 text-center">
        <div className="d-flex flex-column flex-md-row gap-3 justify-content-center mb-3">
          <Button
            label={saveStatus.saving ? "Saving..." : "Save Configuration"}
            color="gray"
            onClick={() => handleSave("save_config")}
            disabled={saveStatus.saving}
          />
          <Button
            label={saveStatus.saving ? "Enabling..." : "Enable Economy Now"}
            color="gold"
            onClick={() => handleSave("enable_economy")}
            disabled={saveStatus.saving || !canEnableEconomy}
          />
        </div>
        <p className="text-muted small mb-0">
          You can save configuration without enabling the economy, or enable it immediately after configuration.
        </p>
      </div>

      <div className="text-center mt-4">
        <Button label="Back to Admin Panel" color="gray" href="/dashboard" />
      </div>
    </div>
  );
}

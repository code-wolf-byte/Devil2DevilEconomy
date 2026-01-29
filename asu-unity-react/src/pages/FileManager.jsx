import React from "react";
import { Button } from "@asu/unity-react-core";

const buildApiBase = () => {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (isoString) => {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleDateString();
};

export default function FileManager({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [files, setFiles] = React.useState([]);
  const [stats, setStats] = React.useState({ total: 0, images: 0, archives: 0, documents: 0 });
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [uploadStatus, setUploadStatus] = React.useState({ uploading: false, error: null, success: null });
  const [deleteStatus, setDeleteStatus] = React.useState({ deleting: null, error: null });
  const fileInputRef = React.useRef(null);

  const apiBaseUrl = React.useMemo(buildApiBase, []);

  const loadFiles = React.useCallback(async () => {
    try {
      setStatus({ loading: true, error: null });
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/files` : "/api/admin/files";
      const response = await fetch(url, { credentials: "include" });

      if (!response.ok) {
        throw new Error(`Failed to load files (${response.status})`);
      }

      const data = await response.json();
      setFiles(Array.isArray(data.files) ? data.files : []);
      setStats(data.stats || { total: 0, images: 0, archives: 0, documents: 0 });
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
    loadFiles();
  }, [isAuthenticated, isAdmin, loadFiles]);

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadStatus({ uploading: true, error: null, success: null });

    try {
      const formData = new FormData();
      formData.append("file", file);

      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/files` : "/api/admin/files";
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Upload failed (${response.status})`);
      }

      setUploadStatus({ uploading: false, error: null, success: "File uploaded successfully!" });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await loadFiles();
    } catch (error) {
      setUploadStatus({ uploading: false, error: error.message, success: null });
    }
  };

  const handleDelete = async (filePath) => {
    if (!window.confirm("Are you sure you want to delete this file?")) return;

    setDeleteStatus({ deleting: filePath, error: null });

    try {
      const url = apiBaseUrl ? `${apiBaseUrl}/api/admin/files` : "/api/admin/files";
      const response = await fetch(url, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ file_path: filePath }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Delete failed (${response.status})`);
      }

      setDeleteStatus({ deleting: null, error: null });
      await loadFiles();
    } catch (error) {
      setDeleteStatus({ deleting: null, error: error.message });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert("Path copied to clipboard!");
    }).catch(() => {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      alert("Path copied to clipboard!");
    });
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">File Manager</h1>
        <p className="text-muted">Please sign in to access this page.</p>
        <Button label="Sign in with Discord" color="gold" href={loginHref} />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">File Manager</h1>
        <p className="text-danger">You do not have permission to view this page.</p>
        <Button label="Back to Dashboard" color="gray" href="/dashboard" />
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="text-center mb-4">
        <h1 className="display-6 fw-bold mb-2">File Manager</h1>
        <p className="text-muted">Manage digital assets for your products</p>
        <p className="small text-muted">
          Upload, organize, and manage files for Discord roles, Minecraft skins, and digital content
        </p>
      </div>

      <div className="border rounded bg-white p-4 mb-4" style={{ background: "linear-gradient(to right, rgba(25, 135, 84, 0.1), rgba(13, 202, 240, 0.1))" }}>
        <h2 className="h5 fw-bold mb-3 text-success">Upload New File</h2>
        <p className="text-muted small mb-3">Upload files for your digital products</p>

        <div className="mb-3">
          <label className="form-label">Select File</label>
          <input
            type="file"
            className="form-control"
            ref={fileInputRef}
            onChange={handleUpload}
            disabled={uploadStatus.uploading}
          />
          <small className="text-muted">
            Supported: Images, Archives, Documents, Audio, Video, Minecraft files, and more
          </small>
        </div>

        {uploadStatus.uploading && (
          <div className="d-flex align-items-center gap-2 text-muted">
            <div className="spinner-border spinner-border-sm" role="status">
              <span className="visually-hidden">Uploading...</span>
            </div>
            <span>Uploading file...</span>
          </div>
        )}

        {uploadStatus.error && (
          <div className="alert alert-danger mt-3 mb-0">{uploadStatus.error}</div>
        )}
        {uploadStatus.success && (
          <div className="alert alert-success mt-3 mb-0">{uploadStatus.success}</div>
        )}
      </div>

      <div className="border rounded bg-white p-4 mb-4">
        <h2 className="h5 fw-bold mb-3">File Statistics</h2>
        <div className="row g-3">
          <div className="col-6 col-md-3">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-primary mb-1">{stats.total}</div>
              <div className="small text-muted">Total Files</div>
            </div>
          </div>
          <div className="col-6 col-md-3">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-success mb-1">{stats.images}</div>
              <div className="small text-muted">Images</div>
            </div>
          </div>
          <div className="col-6 col-md-3">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-warning mb-1">{stats.archives}</div>
              <div className="small text-muted">Archives</div>
            </div>
          </div>
          <div className="col-6 col-md-3">
            <div className="bg-light rounded p-3 text-center">
              <div className="h4 fw-bold text-info mb-1">{stats.documents}</div>
              <div className="small text-muted">Documents</div>
            </div>
          </div>
        </div>
      </div>

      <div className="border rounded bg-white p-4 mb-4">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h2 className="h5 fw-bold mb-0">Uploaded Files</h2>
          <span className="text-muted">{files.length} file{files.length !== 1 ? "s" : ""} available</span>
        </div>

        {status.loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-warning mb-3" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="text-muted mb-0">Loading files...</p>
          </div>
        ) : status.error ? (
          <div className="alert alert-danger">{status.error}</div>
        ) : files.length === 0 ? (
          <div className="text-center py-5">
            <div className="display-1 text-muted mb-3">&#128193;</div>
            <h3 className="h5 fw-semibold mb-2">No files uploaded yet</h3>
            <p className="text-muted">Upload your first digital asset to get started!</p>
          </div>
        ) : (
          <div className="d-flex flex-column gap-3">
            {deleteStatus.error && (
              <div className="alert alert-danger">{deleteStatus.error}</div>
            )}
            {files.map((file) => (
              <div key={file.path} className="border rounded p-3 bg-light">
                <div className="d-flex align-items-start gap-3">
                  {file.is_image ? (
                    <img
                      src={file.path}
                      alt={file.name}
                      className="rounded"
                      style={{ width: "64px", height: "64px", objectFit: "cover" }}
                    />
                  ) : (
                    <div
                      className="rounded bg-secondary d-flex align-items-center justify-content-center text-white"
                      style={{ width: "64px", height: "64px" }}
                    >
                      {file.is_archive ? "&#128230;" : file.is_document ? "&#128196;" : "&#128196;"}
                    </div>
                  )}
                  <div className="flex-grow-1">
                    <h3 className="h6 fw-semibold mb-1">{file.name}</h3>
                    <p className="small text-muted mb-2">
                      <code className="bg-dark text-light px-2 py-1 rounded small">{file.path}</code>
                    </p>
                    <div className="d-flex align-items-center justify-content-between mb-2 text-muted small">
                      <span>{formatFileSize(file.size)}</span>
                      <span>{formatDate(file.modified)}</span>
                    </div>
                    <div className="d-flex flex-wrap gap-2">
                      <a
                        href={file.path}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-sm btn-primary"
                      >
                        View
                      </a>
                      <button
                        type="button"
                        className="btn btn-sm btn-success"
                        onClick={() => copyToClipboard(file.path)}
                      >
                        Copy Path
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(file.path)}
                        disabled={deleteStatus.deleting === file.path}
                      >
                        {deleteStatus.deleting === file.path ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="text-center d-flex flex-wrap gap-3 justify-content-center">
        <Button label="Back to Admin Panel" color="gray" href="/dashboard" />
        <Button label="Digital Templates" color="gold" href="/digital-templates" />
      </div>
    </div>
  );
}

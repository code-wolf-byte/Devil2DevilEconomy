import { useMemo } from "react";

/**
 * Builds the API base URL from VITE_API_BASE_URL, stripping any trailing /api suffix.
 * Returns an empty string when running against the same origin (dev proxy or same-host deploy).
 */
export function buildApiBase() {
  const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  if (!value) return "";
  return value.endsWith("/api") ? value.slice(0, -4) : value;
}

/**
 * Returns a memoized function that prepends the API base URL to a path.
 * Usage in a component:
 *   const url = useApiUrl();
 *   fetch(url("/api/products"))
 */
export function useApiUrl() {
  const base = useMemo(buildApiBase, []);
  return useMemo(() => (path) => (base ? `${base}${path}` : path), [base]);
}

/**
 * Default fetch options for API calls (includes credentials when using a remote base URL).
 */
export function apiFetch(url, options = {}) {
  const base = buildApiBase();
  const fullUrl = base ? `${base}${url}` : url;
  return fetch(fullUrl, {
    ...(base ? { credentials: "include" } : {}),
    ...options,
  });
}

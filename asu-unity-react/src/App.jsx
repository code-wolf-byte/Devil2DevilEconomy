import React, { useEffect, useLayoutEffect, useMemo, useState } from "react";
import Header from "./components/Header";
import Footer from "./components/footer";
import HowToEarn from "./pages/HowToEarn";
import AdminProducts from "./pages/AdminProducts";
import Dashboard from "./pages/Dashboard";
import Leaderboard from "./pages/Leaderboard";
import MyPurchases from "./pages/MyPurchases";
import Product from "./pages/Product";
import Store from "./pages/Store";
import "./App.css";

export default function App() {
  const normalizePath = (value) => {
    if (!value) return "/";
    const cleaned = value.replace(/\/+$/, "");
    return cleaned === "" ? "/" : cleaned;
  };

  const [path, setPath] = useState(() => normalizePath(window.location.pathname));
  const [authState, setAuthState] = useState({
    loading: true,
    authenticated: false,
    user: null,
    isAdmin: false,
  });
  const apiBaseUrl = useMemo(() => {
    const value = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
    if (!value) return "";
    return value.endsWith("/api") ? value.slice(0, -4) : value;
  }, []);

  const withBase = (path) => (apiBaseUrl ? `${apiBaseUrl}${path}` : path);

  useEffect(() => {
    const handlePopState = () => setPath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // ✅ Measure ASU header height and offset main content by that amount
  const [headerOffset, setHeaderOffset] = useState(0);

  useLayoutEffect(() => {
    const el = document.getElementById("asuHeader");
    if (!el) return;

    const update = () => {
      // Use offsetHeight so it matches layout flow
      setHeaderOffset(el.offsetHeight || 0);
    };

    update();

    // Keep it updated when header changes size (mobile menu, title expand, etc.)
    const ro = new ResizeObserver(update);
    ro.observe(el);

    window.addEventListener("resize", update);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", update);
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadAuth = async () => {
      try {
        const response = await fetch(
          withBase("/api/me"),
          apiBaseUrl ? { credentials: "include" } : {}
        );
        if (!response.ok) {
          throw new Error(`Auth request failed (${response.status})`);
        }
        const data = await response.json();
        if (isMounted) {
          setAuthState({
            loading: false,
            authenticated: Boolean(data.authenticated),
            user: data.user || null,
            isAdmin: Boolean(data.user?.is_admin),
          });
        }
      } catch (error) {
        if (isMounted) {
          setAuthState({
            loading: false,
            authenticated: false,
            user: null,
            isAdmin: false,
          });
        }
      }
    };

    loadAuth();
    const handleFocus = () => loadAuth();
    window.addEventListener("focus", handleFocus);
    return () => {
      isMounted = false;
      window.removeEventListener("focus", handleFocus);
    };
  }, [apiBaseUrl]);

  const content = useMemo(() => {
    if (path === "/how-to-earn") {
      return <HowToEarn />;
    }

    if (path === "/leaderboard") {
      return <Leaderboard />;
    }

    if (path === "/my-purchases") {
      return (
        <MyPurchases
          isAuthenticated={authState.authenticated}
          loginHref={withBase("/auth/login")}
        />
      );
    }

    if (path === "/store" || path === "/") {
      return (
        <Store
          isAuthenticated={authState.authenticated}
          isAdmin={authState.isAdmin}
          userName={authState.user?.username || ""}
          balance={authState.user?.balance ?? 0}
          avatarUrl={authState.user?.avatar_url || ""}
        />
      );
    }

    if (path === "/dashboard") {
      return (
        <Dashboard
          isAuthenticated={authState.authenticated}
          isAdmin={authState.isAdmin}
          userName={authState.user?.username || ""}
          loginHref={withBase("/auth/login")}
          storeHref="/store"
        />
      );
    }

    if (path === "/admin/products" || path === "/admin/products/new") {
      return (
        <AdminProducts
          isAuthenticated={authState.authenticated}
          isAdmin={authState.isAdmin}
          loginHref={withBase("/auth/login")}
        />
      );
    }

    if (path.startsWith("/admin/products/")) {
      return (
        <AdminProducts
          isAuthenticated={authState.authenticated}
          isAdmin={authState.isAdmin}
          loginHref={withBase("/auth/login")}
        />
      );
    }

    if (path.startsWith("/product/")) {
      const productId = Number.parseInt(path.split("/")[2], 10);
      if (Number.isFinite(productId)) {
        return <Product productId={productId} />;
      }
    }

    return (
      <div className="container py-5">
        <h1 className="display-5 fw-bold mb-3">Devil2Devil Economy</h1>
        <p className="lead text-muted">
          Explore the community marketplace and learn how to earn and use
          pitchforks.
        </p>
      </div>
    );
  }, [path, authState.authenticated, authState.isAdmin, authState.user?.username]);

  return (
    <div className="main-container">
      <Header
      />
      {/* ✅ Push content below sticky/overlay header */}
      <main className="main-content" style={{ paddingTop: headerOffset }}>
        {content}
      </main>
      <Footer />
    </div>
  );
}

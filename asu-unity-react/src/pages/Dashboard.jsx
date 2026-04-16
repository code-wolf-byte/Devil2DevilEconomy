import React from "react";
import {
  Coins,
  TrendingUp,
  MessageSquare,
  Mic,
  Store,
  Package,
  Tag,
  Plus,
  Palette,
  FolderOpen,
  Settings,
  ShoppingBag,
  Trophy,
  ArrowLeft,
  User,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiUrl } from "@/utils/api";

const QUICK_ACTIONS = [
  { href: "/store",              icon: Store,      label: "Visit Shop",         primary: true },
  { href: "/admin/products",     icon: Package,    label: "Manage Products" },
  { href: "/admin/categories",   icon: Tag,        label: "Categories" },
  { href: "/admin/products/new", icon: Plus,       label: "Add Product" },
  { href: "/digital-templates",  icon: Palette,    label: "Digital Templates" },
  { href: "/file-manager",       icon: FolderOpen, label: "File Manager" },
  { href: "/economy-config",     icon: Settings,   label: "Economy Config" },
  { href: "/admin-purchases",    icon: ShoppingBag,label: "View Purchases" },
  { href: "/admin-leaderboard",  icon: Trophy,     label: "View Leaderboard" },
];

function StatCard({ icon: Icon, label, value, colorClass }) {
  return (
    <Card>
      <CardContent className="p-5 flex items-center gap-4">
        <div className={`rounded-lg p-2.5 ${colorClass}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value ?? 0}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="container py-5 space-y-6">
      <Skeleton className="h-24 w-full" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}

export default function Dashboard({
  isAuthenticated = false,
  isAdmin = false,
  userName = "",
  loginHref = "/auth/login",
  storeHref = "/store",
}) {
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [dashboardData, setDashboardData] = React.useState(null);
  const [products, setProducts] = React.useState([]);
  const [productsStatus, setProductsStatus] = React.useState({ loading: true, error: null });

  const url = useApiUrl();

  React.useEffect(() => {
    let isMounted = true;
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      setDashboardData(null);
      setProducts([]);
      setProductsStatus({ loading: false, error: null });
      return;
    }

    const loadDashboard = async () => {
      try {
        const response = await fetch(url("/api/dashboard"), { credentials: "include" });
        if (!response.ok) throw new Error(`Dashboard request failed (${response.status})`);
        const data = await response.json();
        if (isMounted) {
          setDashboardData(data);
          setStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) setStatus({ loading: false, error: error.message });
      }
    };

    const loadProducts = async () => {
      try {
        setProductsStatus({ loading: true, error: null });
        const response = await fetch(url("/api/admin/products"), { credentials: "include" });
        if (!response.ok) throw new Error(`Products request failed (${response.status})`);
        const data = await response.json();
        if (isMounted) {
          setProducts(Array.isArray(data.products) ? data.products : []);
          setProductsStatus({ loading: false, error: null });
        }
      } catch (error) {
        if (isMounted) setProductsStatus({ loading: false, error: error.message });
      }
    };

    loadDashboard();
    loadProducts();
    return () => { isMounted = false; };
  }, [url, isAuthenticated, isAdmin]);

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <p className="text-gray-500 mb-4">Please sign in to access this page.</p>
        <a href={loginHref} className="btn btn-warning">Sign in with Discord</a>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <p className="text-red-600 mb-4">You do not have permission to view this page.</p>
        <a href={storeHref} className="btn btn-secondary">Back to Store</a>
      </div>
    );
  }

  if (status.loading) return <LoadingSkeleton />;

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Admin Dashboard</h1>
        <Card className="border-red-200 bg-red-50 mb-4">
          <CardContent className="p-4 text-red-700 text-sm">Failed to load dashboard: {status.error}</CardContent>
        </Card>
        <a href={storeHref} className="btn btn-secondary">Back to Store</a>
      </div>
    );
  }

  const achievements = dashboardData?.achievements || [];
  const recentPurchases = dashboardData?.recent_purchases || [];
  const dashboardUser = dashboardData?.user || {};

  const formatTimestamp = (value) => {
    if (!value) return "";
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
  };

  return (
    <div className="container py-5 space-y-6">
      {/* Profile header */}
      <Card>
        <CardContent className="p-6 flex items-center gap-4">
          {dashboardUser.avatar_url ? (
            <img
              src={dashboardUser.avatar_url}
              alt={dashboardUser.username || userName || "User avatar"}
              className="w-16 h-16 rounded-full object-cover shrink-0"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
              <User className="h-7 w-7 text-gray-400" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-gray-900 truncate">
              Welcome back, {dashboardUser.username || userName || "Admin"}!
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">Here&apos;s your economy overview.</p>
          </div>
          <a href={storeHref}>
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4" />
              Back to Store
            </Button>
          </a>
        </CardContent>
      </Card>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Coins}        label="Current Balance"      value={dashboardUser.balance}       colorClass="bg-yellow-100 text-yellow-600" />
        <StatCard icon={TrendingUp}   label="Total Points Earned"  value={dashboardUser.points}        colorClass="bg-green-100 text-green-600" />
        <StatCard icon={MessageSquare}label="Messages Sent"        value={dashboardUser.message_count} colorClass="bg-blue-100 text-blue-600" />
        <StatCard icon={Mic}          label="Voice Minutes"        value={dashboardUser.voice_minutes} colorClass="bg-purple-100 text-purple-600" />
      </div>

      {/* Achievements + Recent Purchases */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="h-full">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Achievements</CardTitle>
              <Badge variant="warning">{achievements.length} Unlocked</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {achievements.length ? (
              <div className="flex flex-col gap-3">
                {achievements.map((a) => (
                  <div key={a.id} className="rounded-lg bg-gray-50 p-3">
                    <p className="font-semibold text-sm text-gray-900">{a.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{a.description}</p>
                    <p className="text-xs font-semibold text-yellow-600 mt-1">+{a.points} points</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">
                No achievements yet. Keep participating!
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Recent Purchases</CardTitle>
              <a href={storeHref}>
                <Button size="sm" className="bg-yellow-500 hover:bg-yellow-600 text-white">
                  <Store className="h-3.5 w-3.5" /> Shop
                </Button>
              </a>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {recentPurchases.length ? (
              <div className="flex flex-col gap-3">
                {recentPurchases.map((purchase) => (
                  <div key={purchase.id} className="flex items-center gap-3 rounded-lg bg-gray-50 p-3">
                    {purchase.image_url ? (
                      <img
                        src={purchase.image_url}
                        alt={purchase.product_name}
                        className="w-12 h-12 rounded object-cover shrink-0"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded bg-gray-200 flex items-center justify-center shrink-0">
                        <Package className="h-5 w-5 text-gray-400" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-gray-900 truncate">{purchase.product_name}</p>
                      <p className="text-xs text-gray-500">{formatTimestamp(purchase.timestamp)}</p>
                      <p className="text-xs font-semibold text-red-600 mt-0.5">-{purchase.points_spent} points</p>
                      {purchase.download_url && (
                        <a href={purchase.download_url} className="btn btn-sm btn-success mt-1 py-0 px-2 text-xs">
                          Download
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">
                No purchases yet. Visit the shop to buy your first item!
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {QUICK_ACTIONS.map(({ href, icon: Icon, label, primary }) => (
              <a
                key={href}
                href={href}
                className={`flex flex-col items-center gap-2 rounded-lg p-4 text-center text-sm font-medium transition-colors no-underline ${
                  primary
                    ? "bg-yellow-500 text-white hover:bg-yellow-600"
                    : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                }`}
              >
                <Icon className="h-5 w-5" />
                {label}
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Products list */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Products</CardTitle>
            <a href="/admin/products/new">
              <Button size="sm" className="bg-yellow-500 hover:bg-yellow-600 text-white">
                <Plus className="h-4 w-4" /> Add Product
              </Button>
            </a>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {productsStatus.error && (
            <div className="text-sm text-red-600 bg-red-50 rounded p-3 mb-3">{productsStatus.error}</div>
          )}
          {productsStatus.loading ? (
            <div className="flex flex-col gap-2">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14" />)}
            </div>
          ) : products.length ? (
            <div className="flex flex-col divide-y rounded-lg border overflow-hidden">
              {products.map((product) => (
                <a
                  key={product.id}
                  href={`/admin/products/${product.id}`}
                  className="flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors no-underline"
                >
                  {product.image_url ? (
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-11 h-11 rounded object-cover shrink-0"
                    />
                  ) : (
                    <div className="w-11 h-11 rounded bg-gray-100 flex items-center justify-center shrink-0">
                      <Package className="h-5 w-5 text-gray-400" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-gray-900 truncate">{product.name}</p>
                    <p className="text-xs text-gray-500">
                      {product.is_active ? (
                        <span className="text-green-600">Active</span>
                      ) : (
                        <span className="text-gray-400">Archived</span>
                      )} · {product.price} pts
                    </p>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-6">No products yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

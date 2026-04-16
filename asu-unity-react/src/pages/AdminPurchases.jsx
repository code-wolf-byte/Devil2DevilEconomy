import React from "react";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Package,
  ShoppingBag,
  RefreshCw,
  User,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiUrl } from "@/utils/api";

function LoadingSkeleton() {
  return (
    <div className="container py-5 space-y-6">
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
      <Skeleton className="h-96" />
    </div>
  );
}

function Avatar({ src, alt, size = "sm" }) {
  const cls = size === "sm" ? "w-8 h-8" : "w-10 h-10";
  return src ? (
    <img src={src} alt={alt} className={`${cls} rounded-full object-cover border-2 border-yellow-400 shrink-0`} />
  ) : (
    <div className={`${cls} rounded-full bg-gray-100 border-2 border-yellow-400 flex items-center justify-center shrink-0`}>
      <User className="h-4 w-4 text-gray-400" />
    </div>
  );
}

function ProductThumb({ src, alt }) {
  return src ? (
    <img src={src} alt={alt} className="w-10 h-10 rounded object-cover shrink-0" />
  ) : (
    <div className="w-10 h-10 rounded bg-gray-100 flex items-center justify-center shrink-0">
      <Package className="h-4 w-4 text-gray-400" />
    </div>
  );
}

export default function AdminPurchases({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [data, setData] = React.useState(null);
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [currentPage, setCurrentPage] = React.useState(1);

  const url = useApiUrl();

  const loadData = React.useCallback(async (page = 1) => {
    try {
      setStatus({ loading: true, error: null });
      const response = await fetch(url(`/api/admin/purchases?page=${page}`), { credentials: "include" });
      if (!response.ok) throw new Error(`Failed to load purchases (${response.status})`);
      const result = await response.json();
      setData(result);
      setCurrentPage(page);
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
    loadData(1);
  }, [isAuthenticated, isAdmin, loadData]);

  const formatDate = (iso) => iso ? new Date(iso).toLocaleDateString() : "";
  const formatTime = (iso) => iso ? new Date(iso).toLocaleTimeString() : "";

  const pageNums = (() => {
    const pagination = data?.pagination;
    if (!pagination || pagination.pages <= 1) return [];
    const total = pagination.pages;
    const cur = currentPage;
    if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1);
    if (cur <= 3) return [1, 2, 3, 4, 5];
    if (cur >= total - 2) return [total - 4, total - 3, total - 2, total - 1, total];
    return [cur - 2, cur - 1, cur, cur + 1, cur + 2];
  })();

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <p className="text-gray-500 mb-4">Please sign in to access this page.</p>
        <a href={loginHref} className="btn btn-warning">Sign in with Discord</a>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <p className="text-red-600 mb-4">You do not have permission to view this page.</p>
        <a href="/dashboard" className="btn btn-secondary">Back to Dashboard</a>
      </div>
    );
  }

  if (status.loading) return <LoadingSkeleton />;

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Purchase History</h1>
        <Card className="border-red-200 bg-red-50 mb-4">
          <CardContent className="p-4 text-red-700 text-sm">{status.error}</CardContent>
        </Card>
        <Button onClick={() => loadData(currentPage)}>
          <RefreshCw className="h-4 w-4" /> Retry
        </Button>
      </div>
    );
  }

  const { purchases = [], stats, pagination } = data || {};

  return (
    <div className="container py-5 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Purchase History</h1>
          <p className="text-sm text-gray-500 mt-1">All user purchases and transactions</p>
        </div>
        <a href="/dashboard">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4" /> Back to Dashboard
          </Button>
        </a>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Purchases", value: pagination?.total ?? 0,              color: "text-yellow-600" },
          { label: "Points on Page",  value: stats?.total_points_on_page ?? 0,    color: "text-green-600" },
          { label: "Current Page",    value: pagination?.page ?? 1,               color: "text-blue-600" },
          { label: "Total Pages",     value: pagination?.pages ?? 1,              color: "text-purple-600" },
        ].map(({ label, value, color }) => (
          <Card key={label}>
            <CardContent className="p-5 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-1">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {purchases.length === 0 ? (
        <Card>
          <CardContent className="p-16 text-center">
            <ShoppingBag className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-600 mb-1">No Purchases Found</h3>
            <p className="text-sm text-gray-400">No purchase history available yet.</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader className="pb-0">
            <CardTitle className="text-base">Purchase Records</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {/* Desktop table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left">
                    {["User", "Product", "Points", "Date", "UUID"].map((h) => (
                      <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {purchases.map((purchase) => (
                    <tr key={purchase.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <Avatar src={purchase.user.avatar_url} alt={purchase.user.username} />
                          <div>
                            <p className="font-medium text-gray-900">{purchase.user.username}</p>
                            <p className="text-xs text-gray-400">ID: {purchase.user.discord_id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <ProductThumb src={purchase.product.image_url} alt={purchase.product.name} />
                          <div>
                            <p className="font-medium text-gray-900">{purchase.product.name}</p>
                            <p className="text-xs text-gray-400 truncate max-w-[160px]">{purchase.product.description}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-bold text-yellow-600">{purchase.points_spent}</td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-gray-900">{formatDate(purchase.timestamp)}</p>
                        <p className="text-xs text-gray-400">{formatTime(purchase.timestamp)}</p>
                      </td>
                      <td className="px-4 py-3">
                        {purchase.user.user_uuid ? (
                          <code className="text-xs bg-gray-900 text-green-400 px-2 py-1 rounded">
                            {purchase.user.user_uuid.substring(0, 8)}…
                          </code>
                        ) : (
                          <span className="text-xs text-gray-400">No UUID</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden flex flex-col divide-y">
              {purchases.map((purchase) => (
                <div key={purchase.id} className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Avatar src={purchase.user.avatar_url} alt={purchase.user.username} size="md" />
                      <div>
                        <p className="font-semibold text-gray-900">{purchase.user.username}</p>
                        <p className="text-xs text-gray-400">{formatDate(purchase.timestamp)} {formatTime(purchase.timestamp)}</p>
                      </div>
                    </div>
                    <p className="text-lg font-bold text-yellow-600">{purchase.points_spent}</p>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <ProductThumb src={purchase.product.image_url} alt={purchase.product.name} />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-gray-900">{purchase.product.name}</p>
                      <p className="text-xs text-gray-400 truncate">{purchase.product.description}</p>
                    </div>
                  </div>
                  {purchase.user.user_uuid && (
                    <div className="bg-gray-50 rounded p-2">
                      <p className="text-xs text-gray-400 mb-0.5">UUID</p>
                      <code className="text-xs text-green-700 break-all">{purchase.user.user_uuid}</code>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Pagination */}
            {pagination && pagination.pages > 1 && (
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 border-t">
                <p className="text-sm text-gray-500">
                  Showing {(pagination.page - 1) * pagination.per_page + 1}–
                  {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total}
                </p>
                <div className="flex items-center gap-1">
                  {pagination.has_prev && (
                    <Button variant="outline" size="icon" onClick={() => loadData(1)}>
                      <ChevronsLeft className="h-4 w-4" />
                    </Button>
                  )}
                  <Button variant="outline" size="icon" disabled={!pagination.has_prev} onClick={() => loadData(pagination.prev_num)}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  {pageNums.map((n) => (
                    <Button key={n} size="sm" variant={n === currentPage ? "default" : "outline"} onClick={() => loadData(n)}>
                      {n}
                    </Button>
                  ))}
                  <Button variant="outline" size="icon" disabled={!pagination.has_next} onClick={() => loadData(pagination.next_num)}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                  {pagination.has_next && (
                    <Button variant="outline" size="icon" onClick={() => loadData(pagination.pages)}>
                      <ChevronsRight className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

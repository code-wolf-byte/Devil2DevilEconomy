import React from "react";
import {
  Users,
  Coins,
  ShoppingCart,
  Package,
  Trophy,
  TrendingUp,
  Medal,
  ShoppingBag,
  Flame,
  ArrowLeft,
  Shield,
  Star,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiUrl } from "@/utils/api";

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

function RankList({ title, icon: Icon, iconClass, items, renderLeft, renderRight }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Icon className={`h-4 w-4 ${iconClass}`} />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0 flex flex-col gap-2">
        {items.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-4">No data yet</p>
        )}
        {items.map((item, index) => (
          <div
            key={item.user.id}
            className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2"
          >
            <div className="flex items-center gap-3">
              <span className={`text-sm font-bold w-5 text-center ${iconClass}`}>
                {index + 1}
              </span>
              {renderLeft(item)}
            </div>
            {renderRight(item)}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="container py-5 space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
      <Skeleton className="h-96" />
    </div>
  );
}

export default function AdminLeaderboard({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
}) {
  const [data, setData] = React.useState(null);
  const [status, setStatus] = React.useState({ loading: true, error: null });
  const [currentPage, setCurrentPage] = React.useState(1);

  const url = useApiUrl();

  const loadData = React.useCallback(
    async (page = 1) => {
      try {
        setStatus({ loading: true, error: null });
        const response = await fetch(url(`/api/admin/leaderboard?page=${page}`), {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error(`Failed to load leaderboard (${response.status})`);
        }
        const result = await response.json();
        setData(result);
        setCurrentPage(page);
        setStatus({ loading: false, error: null });
      } catch (err) {
        setStatus({ loading: false, error: err.message });
      }
    },
    [url]
  );

  React.useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      return;
    }
    loadData(1);
  }, [isAuthenticated, isAdmin, loadData]);

  const formatDate = (iso) => {
    if (!iso) return null;
    return new Date(iso).toLocaleDateString();
  };

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <p className="text-gray-500 mb-4">Please sign in to access this page.</p>
        <a href={loginHref} className="btn btn-warning">Sign in with Discord</a>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <p className="text-red-600 mb-4">You do not have permission to view this page.</p>
        <a href="/dashboard" className="btn btn-secondary">Back to Dashboard</a>
      </div>
    );
  }

  if (status.loading) return <LoadingSkeleton />;

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">Economy Leaderboard</h1>
        <Card className="border-red-200 bg-red-50 mb-4">
          <CardContent className="p-4 text-red-700 text-sm">{status.error}</CardContent>
        </Card>
        <Button onClick={() => loadData(currentPage)}>
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  const { economy_stats, leaderboard_stats = [], top_spenders = [], most_active = [], pagination } = data || {};

  const pageNums = (() => {
    if (!pagination || pagination.pages <= 1) return [];
    const total = pagination.pages;
    const cur = currentPage;
    if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1);
    if (cur <= 3) return [1, 2, 3, 4, 5];
    if (cur >= total - 2) return [total - 4, total - 3, total - 2, total - 1, total];
    return [cur - 2, cur - 1, cur, cur + 1, cur + 2];
  })();

  return (
    <div className="container py-5 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Economy Leaderboard</h1>
          <p className="text-sm text-gray-500 mt-1">Community statistics and top performers</p>
        </div>
        <a href="/dashboard">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </a>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard icon={Users}        label="Total Users"        value={economy_stats?.total_users}        colorClass="bg-blue-100 text-blue-600" />
        <StatCard icon={Coins}        label="Total Balance"      value={economy_stats?.total_balance}      colorClass="bg-yellow-100 text-yellow-600" />
        <StatCard icon={ShoppingCart} label="Total Spent"        value={economy_stats?.total_spent}        colorClass="bg-red-100 text-red-600" />
        <StatCard icon={Package}      label="Purchases"          value={economy_stats?.total_purchases}    colorClass="bg-purple-100 text-purple-600" />
        <StatCard icon={Trophy}       label="Achievements"       value={economy_stats?.total_achievements} colorClass="bg-orange-100 text-orange-600" />
        <StatCard icon={TrendingUp}   label="Avg Balance"        value={economy_stats?.average_balance}    colorClass="bg-green-100 text-green-600" />
      </div>

      {/* Top 3 panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <RankList
          title="Top Balances"
          icon={Medal}
          iconClass="text-yellow-500"
          items={leaderboard_stats.slice(0, 10)}
          renderLeft={(s) => (
            <div>
              <p className="text-sm font-semibold text-gray-900">{s.user.username}</p>
              <p className="text-xs text-gray-400">{s.achievement_count} achievements</p>
            </div>
          )}
          renderRight={(s) => (
            <div className="text-right">
              <p className="text-sm font-bold text-yellow-600">{s.user.balance ?? 0}</p>
              <p className="text-xs text-gray-400">pitchforks</p>
            </div>
          )}
        />

        <RankList
          title="Top Spenders"
          icon={ShoppingBag}
          iconClass="text-red-500"
          items={top_spenders}
          renderLeft={(s) => (
            <div>
              <p className="text-sm font-semibold text-gray-900">{s.user.username}</p>
              <p className="text-xs text-gray-400">{s.purchase_count} purchases</p>
            </div>
          )}
          renderRight={(s) => (
            <div className="text-right">
              <p className="text-sm font-bold text-red-600">{s.total_spent}</p>
              <p className="text-xs text-gray-400">spent</p>
            </div>
          )}
        />

        <RankList
          title="Most Active"
          icon={Flame}
          iconClass="text-orange-500"
          items={most_active}
          renderLeft={(s) => (
            <div>
              <p className="text-sm font-semibold text-gray-900">{s.user.username}</p>
              <p className="text-xs text-gray-400">{s.user.message_count ?? 0} messages</p>
            </div>
          )}
          renderRight={(s) => (
            <div className="text-right">
              <p className="text-sm font-bold text-orange-500">{s.activity_score}</p>
              <p className="text-xs text-gray-400">activity</p>
            </div>
          )}
        />
      </div>

      {/* Detailed leaderboard table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Detailed Leaderboard</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {/* Desktop table */}
          <div className="hidden lg:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left">
                  {["Rank", "User", "Balance", "Spent", "Purchases", "Achievements", "Messages", "Voice", "Activity"].map((h) => (
                    <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {leaderboard_stats.map((stat) => (
                  <tr key={stat.user.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <span className={`font-bold ${stat.rank <= 3 ? "text-yellow-500" : "text-gray-700"}`}>
                        {stat.rank <= 3 && <Trophy className="inline h-3.5 w-3.5 mr-1" />}
                        {stat.rank}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={`/admin/users/${stat.user.id}`}
                        className="font-semibold text-gray-900 hover:text-yellow-600 transition-colors no-underline"
                      >
                        {stat.user.username}
                      </a>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        {stat.user.is_admin && (
                          <Badge variant="secondary" className="text-xs py-0 px-1.5 gap-0.5">
                            <Shield className="h-3 w-3" /> Admin
                          </Badge>
                        )}
                        {stat.user.has_boosted && (
                          <Badge variant="warning" className="text-xs py-0 px-1.5 gap-0.5">
                            <Star className="h-3 w-3" /> Booster
                          </Badge>
                        )}
                        {stat.user.created_at && (
                          <span className="text-xs text-gray-400">Joined {formatDate(stat.user.created_at)}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 font-bold text-yellow-600">{stat.user.balance ?? 0}</td>
                    <td className="px-4 py-3 font-bold text-red-600">{stat.total_spent}</td>
                    <td className="px-4 py-3 font-bold text-purple-600">{stat.purchase_count}</td>
                    <td className="px-4 py-3 font-bold text-orange-500">{stat.achievement_count}</td>
                    <td className="px-4 py-3 font-bold text-green-600">{stat.user.message_count ?? 0}</td>
                    <td className="px-4 py-3 font-bold text-blue-600">{stat.user.voice_minutes ?? 0}m</td>
                    <td className="px-4 py-3 font-bold text-gray-700">{stat.activity_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="lg:hidden flex flex-col divide-y">
            {leaderboard_stats.map((stat) => (
              <div key={stat.user.id} className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className={`text-xl font-bold ${stat.rank <= 3 ? "text-yellow-500" : "text-gray-400"}`}>
                      #{stat.rank}
                    </span>
                    <div>
                      <a
                        href={`/admin/users/${stat.user.id}`}
                        className="font-semibold text-gray-900 hover:text-yellow-600 no-underline"
                      >
                        {stat.user.username}
                      </a>
                      <div className="flex gap-1 mt-0.5">
                        {stat.user.is_admin && <Badge variant="secondary" className="text-xs py-0">Admin</Badge>}
                        {stat.user.has_boosted && <Badge variant="warning" className="text-xs py-0">Booster</Badge>}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-yellow-600">{stat.user.balance ?? 0}</p>
                    <p className="text-xs text-gray-400">pitchforks</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {[
                    { label: "Spent", value: stat.total_spent, color: "text-red-600" },
                    { label: "Purchases", value: stat.purchase_count, color: "text-purple-600" },
                    { label: "Achievements", value: stat.achievement_count, color: "text-orange-500" },
                    { label: "Activity", value: stat.activity_score, color: "text-gray-700" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-gray-50 rounded p-2">
                      <p className="text-xs text-gray-400">{label}</p>
                      <p className={`font-bold ${color}`}>{value}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination && pagination.pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 border-t">
              <p className="text-sm text-gray-500">
                Showing {(pagination.page - 1) * pagination.per_page + 1}–
                {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} users
              </p>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  disabled={!pagination.has_prev}
                  onClick={() => loadData(pagination.prev_num)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                {pageNums.map((n) => (
                  <Button
                    key={n}
                    size="sm"
                    variant={n === currentPage ? "default" : "outline"}
                    onClick={() => loadData(n)}
                  >
                    {n}
                  </Button>
                ))}
                <Button
                  variant="outline"
                  size="icon"
                  disabled={!pagination.has_next}
                  onClick={() => loadData(pagination.next_num)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

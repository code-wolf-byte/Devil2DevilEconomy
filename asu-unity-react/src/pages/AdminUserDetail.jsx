import React from "react";
import {
  ArrowLeft,
  MessageSquare,
  Heart,
  Mic,
  Calendar,
  Camera,
  Users,
  Trophy,
  Shield,
  Star,
  GraduationCap,
  Building,
  Cake,
  Zap,
  Package,
  Dice5,
  ShoppingCart,
  TrendingUp,
  RefreshCw,
  User,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useApiUrl } from "@/utils/api";

const EARNING_ROWS = [
  { key: "messages",          label: "Messages Sent",      icon: MessageSquare, color: "text-blue-600",   bg: "bg-blue-50" },
  { key: "reactions",         label: "Reactions Given",    icon: Heart,         color: "text-red-500",    bg: "bg-red-50" },
  { key: "voice_minutes",     label: "Voice Minutes",      icon: Mic,           color: "text-purple-600", bg: "bg-purple-50" },
  { key: "daily_claims",      label: "Daily Claims",       icon: Calendar,      color: "text-green-600",  bg: "bg-green-50" },
  { key: "campus_photos",     label: "Campus Photos",      icon: Camera,        color: "text-yellow-600", bg: "bg-yellow-50" },
  { key: "daily_engagement",  label: "Daily Engagement",   icon: Users,         color: "text-cyan-600",   bg: "bg-cyan-50" },
  { key: "achievements",      label: "Achievements",       icon: Trophy,        color: "text-orange-500", bg: "bg-orange-50" },
];

const CONDITIONAL_EARNING_ROWS = [
  { key: "verification_bonus", label: "Verification Bonus", icon: Shield,         color: "text-green-600",  bg: "bg-green-50" },
  { key: "onboarding_bonus",   label: "Onboarding Bonus",   icon: GraduationCap,  color: "text-blue-600",   bg: "bg-blue-50" },
  { key: "enrollment_deposit", label: "Enrollment Deposit", icon: Building,       color: "text-purple-600", bg: "bg-purple-50" },
  { key: "birthday_bonus",     label: "Birthday Bonus",     icon: Cake,           color: "text-pink-500",   bg: "bg-pink-50" },
  { key: "boost_bonus",        label: "Server Boost Bonus", icon: Zap,            color: "text-indigo-600", bg: "bg-indigo-50" },
];

const SPENDING_ICONS = {
  physical:       { icon: Package,     color: "text-blue-600" },
  role:           { icon: Shield,      color: "text-purple-600" },
  minecraft_skin: { icon: Dice5,       color: "text-green-600" },
  game_code:      { icon: Zap,         color: "text-yellow-600" },
};

function BreakdownRow({ icon: Icon, label, value, color, bg }) {
  return (
    <div className="flex items-center justify-between rounded-lg px-3 py-2 bg-gray-50">
      <div className="flex items-center gap-2.5">
        <div className={`rounded p-1.5 ${bg}`}>
          <Icon className={`h-3.5 w-3.5 ${color}`} />
        </div>
        <span className="text-sm text-gray-700">{label}</span>
      </div>
      <span className={`text-sm font-bold ${color}`}>{value ?? 0}</span>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <Card>
      <CardContent className="p-5 text-center">
        <p className={`text-3xl font-bold ${color}`}>{value ?? "N/A"}</p>
        <p className="text-xs text-gray-500 mt-1">{label}</p>
      </CardContent>
    </Card>
  );
}

function LoadingSkeleton() {
  return (
    <div className="container py-5 space-y-6">
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
    </div>
  );
}

export default function AdminUserDetail({
  isAuthenticated = false,
  isAdmin = false,
  loginHref = "/auth/login",
  userId = null,
}) {
  const [data, setData] = React.useState(null);
  const [status, setStatus] = React.useState({ loading: true, error: null });

  const url = useApiUrl();

  const effectiveUserId = React.useMemo(() => {
    if (userId) return userId;
    const match = window.location.pathname.match(/\/admin\/users\/([^/]+)/);
    return match ? match[1] : null;
  }, [userId]);

  const loadData = React.useCallback(async () => {
    if (!effectiveUserId) {
      setStatus({ loading: false, error: "User ID not provided" });
      return;
    }
    try {
      setStatus({ loading: true, error: null });
      const response = await fetch(url(`/api/admin/users/${effectiveUserId}`), { credentials: "include" });
      if (!response.ok) throw new Error(`Failed to load user details (${response.status})`);
      setData(await response.json());
      setStatus({ loading: false, error: null });
    } catch (err) {
      setStatus({ loading: false, error: err.message });
    }
  }, [url, effectiveUserId]);

  React.useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      setStatus({ loading: false, error: null });
      return;
    }
    loadData();
  }, [isAuthenticated, isAdmin, loadData]);

  const formatDate = (iso) => iso ? new Date(iso).toLocaleDateString() : "Unknown";
  const formatDateTime = (iso) => iso ? new Date(iso).toLocaleString() : "";

  if (!isAuthenticated) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <p className="text-gray-500 mb-4">Please sign in to access this page.</p>
        <a href={loginHref} className="btn btn-warning">Sign in with Discord</a>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <p className="text-red-600 mb-4">You do not have permission to view this page.</p>
        <a href="/dashboard" className="btn btn-secondary">Back to Dashboard</a>
      </div>
    );
  }

  if (status.loading) return <LoadingSkeleton />;

  if (status.error) {
    return (
      <div className="container py-5">
        <h1 className="display-6 fw-bold mb-3">User Details</h1>
        <Card className="border-red-200 bg-red-50 mb-4">
          <CardContent className="p-4 text-red-700 text-sm">{status.error}</CardContent>
        </Card>
        <div className="flex gap-2">
          <Button onClick={loadData}><RefreshCw className="h-4 w-4" /> Retry</Button>
          <a href="/admin-leaderboard"><Button variant="outline"><ArrowLeft className="h-4 w-4" /> Back</Button></a>
        </div>
      </div>
    );
  }

  const { user, stats, earning_breakdown, spending_breakdown, achievements = [], recent_purchases = [], recent_achievements = [] } = data || {};

  return (
    <div className="container py-5 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <a href="/admin-leaderboard">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4" /> Leaderboard
            </Button>
          </a>
          <h1 className="text-2xl font-bold text-gray-900">{user?.username || "Unknown User"}</h1>
          {user?.is_admin && (
            <Badge variant="warning" className="gap-1">
              <Shield className="h-3 w-3" /> Admin
            </Badge>
          )}
          {user?.has_boosted && (
            <Badge variant="secondary" className="gap-1 bg-purple-100 text-purple-700">
              <Star className="h-3 w-3" /> Booster
            </Badge>
          )}
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-yellow-600">{user?.balance ?? 0}</p>
          <p className="text-xs text-gray-400">Current Balance</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Global Rank"    value={stats?.user_rank}      color="text-yellow-600" />
        <StatCard label="Total Earned"   value={stats?.total_earned}   color="text-green-600" />
        <StatCard label="Total Spent"    value={stats?.total_spent}    color="text-red-600" />
        <StatCard label="Activity Score" value={stats?.activity_score} color="text-yellow-600" />
      </div>

      {/* Breakdown cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" /> Points Earned Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 flex flex-col gap-2">
            {EARNING_ROWS.map((row) => (
              <BreakdownRow key={row.key} {...row} value={earning_breakdown?.[row.key]} />
            ))}
            {CONDITIONAL_EARNING_ROWS.filter((r) => (earning_breakdown?.[r.key] ?? 0) > 0).map((row) => (
              <BreakdownRow key={row.key} {...row} value={earning_breakdown?.[row.key]} />
            ))}
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ShoppingCart className="h-4 w-4 text-red-500" /> Points Spent Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {spending_breakdown && Object.keys(spending_breakdown).length > 0 ? (
              <div className="flex flex-col gap-2">
                {Object.entries(spending_breakdown).map(([type, amount]) => {
                  const { icon: Icon, color } = SPENDING_ICONS[type] || { icon: Package, color: "text-gray-500" };
                  return (
                    <div key={type} className="flex items-center justify-between rounded-lg px-3 py-2 bg-gray-50">
                      <div className="flex items-center gap-2.5">
                        <Icon className={`h-4 w-4 ${color}`} />
                        <span className="text-sm text-gray-700 capitalize">{type.replace("_", " ")}</span>
                      </div>
                      <span className="text-sm font-bold text-red-600">{amount}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <ShoppingCart className="h-10 w-10 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No purchases yet</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Achievements */}
      {achievements.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Trophy className="h-4 w-4 text-yellow-500" />
              Achievements
              <Badge variant="warning">{achievements.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {achievements.map((a) => (
                <div key={a.id} className="rounded-lg border border-yellow-200 bg-yellow-50 p-3">
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-semibold text-sm text-yellow-700">{a.name}</p>
                    <span className="text-xs font-bold text-yellow-600">+{a.points}</span>
                  </div>
                  <p className="text-xs text-gray-500">{a.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <ShoppingCart className="h-4 w-4 text-blue-500" /> Recent Purchases
              <span className="text-xs font-normal text-gray-400">(last 30 days)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {recent_purchases.length > 0 ? (
              <div className="flex flex-col gap-2">
                {recent_purchases.map((p) => (
                  <div key={p.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{p.product_name}</p>
                      <p className="text-xs text-gray-400">{formatDateTime(p.timestamp)}</p>
                    </div>
                    <span className="text-sm font-bold text-red-600">-{p.points_spent}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10">
                <ShoppingCart className="h-8 w-8 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No recent purchases</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Trophy className="h-4 w-4 text-yellow-500" /> Recent Achievements
              <span className="text-xs font-normal text-gray-400">(last 30 days)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {recent_achievements.length > 0 ? (
              <div className="flex flex-col gap-2">
                {recent_achievements.map((ua, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <div>
                      <p className="text-sm font-semibold text-yellow-700">{ua.name}</p>
                      <p className="text-xs text-gray-400">{formatDateTime(ua.achieved_at)}</p>
                    </div>
                    <span className="text-sm font-bold text-yellow-600">+{ua.points}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10">
                <Trophy className="h-8 w-8 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No recent achievements</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* User info */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <User className="h-4 w-4 text-gray-500" /> User Information
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: "Discord ID",         value: user?.discord_id || "Not set" },
              { label: "User ID",            value: user?.id || "N/A" },
              { label: "Joined",             value: formatDate(user?.created_at) },
              { label: "Total Purchases",    value: stats?.total_purchases ?? 0 },
              { label: "Total Achievements", value: stats?.total_achievements ?? 0 },
              ...(user?.birthday ? [{ label: "Birthday", value: user.birthday }] : []),
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-gray-400 mb-0.5">{label}</p>
                <p className="text-sm font-semibold text-gray-900">{value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

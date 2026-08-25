import { useAdminMetrics } from "@/hooks/useAdmin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { FileText, Users, MessageSquare, AlertTriangle, Zap, Clock, Search, BarChart3 } from "lucide-react"

function StatCard({ label, value, icon: Icon, sub }: { label: string; value: string | number; icon: React.ElementType; sub?: string }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  )
}

export default function AdminMetricsPage() {
  const { data: metrics, isLoading, error } = useAdminMetrics()

  if (isLoading)
    return (
      <div className="mx-auto max-w-5xl p-6 animate-fade-in space-y-4">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    )
  if (error)
    return (
      <div className="mx-auto max-w-5xl p-6">
        <Card className="border-destructive/30 bg-destructive/10">
          <CardContent className="py-6 text-sm text-destructive">Failed to load metrics</CardContent>
        </Card>
      </div>
    )
  if (!metrics) return null

  return (
    <div className="mx-auto max-w-5xl p-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-primary" /> System Metrics
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Overview of platform health and usage</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Documents" value={metrics.total_documents} icon={FileText} />
        <StatCard label="Users" value={metrics.total_users} icon={Users} />
        <StatCard label="Chat Sessions" value={metrics.total_chat_sessions} icon={MessageSquare} />
        <StatCard label="Errors" value={metrics.error_count} icon={AlertTriangle} />
        <StatCard label="Total Tokens" value={metrics.total_tokens_used.toLocaleString()} icon={Zap} sub="LLM usage" />
        <StatCard label="Avg Chat Latency" value={`${metrics.avg_chat_latency_ms.toFixed(0)}ms`} icon={Clock} />
        <StatCard label="Avg Search Latency" value={`${metrics.avg_search_latency_ms.toFixed(0)}ms`} icon={Search} />
        <StatCard
          label="Health"
          value={metrics.error_count === 0 ? "Healthy" : "Issues"}
          icon={BarChart3}
          sub={`${Object.keys(metrics.documents_by_status).length} statuses`}
        />
      </div>

      {Object.keys(metrics.documents_by_status).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Documents by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {Object.entries(metrics.documents_by_status).map(([status, count]) => (
                <div key={status} className="flex items-center gap-3 rounded-lg border bg-card px-4 py-3 min-w-[140px]">
                  <Badge variant={status === "ready" ? "success" : status === "failed" ? "destructive" : "secondary"} className="capitalize">
                    {status}
                  </Badge>
                  <span className="text-lg font-semibold ml-auto">{count as number}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

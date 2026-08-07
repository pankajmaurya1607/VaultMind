import { useAdminMetrics } from "../hooks/useAdmin"

interface StatCardProps {
  label: string
  value: string | number
  sub?: string
}

function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div className="bg-bg-surface border border-border rounded-xl p-5">
      <p className="text-xs text-text-muted uppercase tracking-wider font-medium mb-1">{label}</p>
      <p className="text-2xl font-semibold text-text">{value}</p>
      {sub && <p className="text-xs text-text-dim mt-0.5">{sub}</p>}
    </div>
  )
}

export default function AdminMetricsPage() {
  const { data: metrics, isLoading, error } = useAdminMetrics()

  if (isLoading) return <div className="p-6 text-sm text-text-muted animate-fade-in">Loading metrics...</div>
  if (error) return <div className="p-6 bg-error/10 border border-error/30 text-error text-sm rounded-lg m-6 animate-fade-in">Failed to load metrics</div>
  if (!metrics) return null

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold text-text mb-6">System Metrics</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Documents" value={metrics.total_documents} />
        <StatCard label="Users" value={metrics.total_users} />
        <StatCard label="Chat Sessions" value={metrics.total_chat_sessions} />
        <StatCard label="Errors" value={metrics.error_count} />
        <StatCard label="Total Tokens Used" value={metrics.total_tokens_used.toLocaleString()} />
        <StatCard label="Avg Chat Latency" value={`${metrics.avg_chat_latency_ms.toFixed(0)}ms`} />
        <StatCard label="Avg Search Latency" value={`${metrics.avg_search_latency_ms.toFixed(0)}ms`} />
      </div>

      {Object.keys(metrics.documents_by_status).length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">Documents by Status</h2>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(metrics.documents_by_status).map(([status, count]) => (
              <div key={status} className="bg-bg-surface border border-border rounded-lg px-4 py-3 min-w-[100px]">
                <p className="text-xs text-text-dim capitalize">{status}</p>
                <p className="text-lg font-semibold text-text">{count as number}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

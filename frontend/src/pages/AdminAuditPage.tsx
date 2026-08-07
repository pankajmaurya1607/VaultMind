import { useAdminAuditLogs } from "../hooks/useAdmin"

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  })
}

export default function AdminAuditPage() {
  const { data: logs, isLoading, error } = useAdminAuditLogs()

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold text-text mb-1">Audit Log</h1>
      <p className="text-sm text-text-muted mb-6">
        {logs ? `${logs.length} event${logs.length !== 1 ? "s" : ""}` : "Loading..."}
      </p>

      {isLoading && <div className="text-sm text-text-muted py-12 text-center">Loading audit logs...</div>}
      {error && <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-3">Failed to load audit logs</div>}

      {logs && logs.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted text-xs uppercase tracking-wider">
                <th className="text-left py-3 pr-4 font-medium">Time</th>
                <th className="text-left py-3 pr-4 font-medium">User</th>
                <th className="text-left py-3 pr-4 font-medium">Action</th>
                <th className="text-left py-3 pr-4 font-medium">Resource</th>
                <th className="text-left py-3 pr-4 font-medium">IP</th>
                <th className="text-left py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-border/50 hover:bg-bg-hover transition-colors">
                  <td className="py-3 pr-4 text-text-muted whitespace-nowrap">{formatDate(log.created_at)}</td>
                  <td className="py-3 pr-4 text-text truncate max-w-[160px]" title={log.user_email || ""}>{log.user_email || "—"}</td>
                  <td className="py-3 pr-4 text-text font-medium">{log.action}</td>
                  <td className="py-3 pr-4 text-text-muted">{log.resource}</td>
                  <td className="py-3 pr-4 text-text-dim font-mono text-xs">{log.ip_address || "—"}</td>
                  <td className="py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      log.success ? "bg-accent/10 text-accent" : "bg-error/10 text-error"
                    }`}>
                      {log.success ? "Success" : "Failed"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

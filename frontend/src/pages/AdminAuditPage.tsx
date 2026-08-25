import { useAdminAuditLogs } from "@/hooks/useAdmin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollText } from "lucide-react"

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
}

export default function AdminAuditPage() {
  const { data: logs, isLoading, error } = useAdminAuditLogs()

  return (
    <div className="mx-auto max-w-6xl p-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <ScrollText className="h-6 w-6 text-primary" /> Audit Log
        </h1>
        <p className="text-sm text-muted-foreground mt-1">{logs ? `${logs.total} event${logs.total !== 1 ? "s" : ""}` : "Loading..."} · Full visibility into who did what</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Activity</CardTitle>
          <CardDescription>Latest 200 audit events</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading && (
            <div className="p-6 space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}
          {error && <div className="mx-6 my-4 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">Failed to load audit logs</div>}
          {logs && logs.items.length === 0 && !isLoading && <div className="py-12 text-center text-sm text-muted-foreground">No audit events yet.</div>}
          {logs && logs.items.length > 0 && (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>IP</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.items.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="whitespace-nowrap text-xs text-muted-foreground">{formatDate(log.created_at)}</TableCell>
                      <TableCell className="max-w-[160px] truncate text-sm" title={log.user_email || ""}>
                        {log.user_email || "—"}
                      </TableCell>
                      <TableCell className="font-medium text-sm">{log.action}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{log.resource}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{log.ip_address || "—"}</TableCell>
                      <TableCell>
                        <Badge variant={log.success ? "success" : "destructive"} className="text-xs">
                          {log.success ? "Success" : "Failed"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

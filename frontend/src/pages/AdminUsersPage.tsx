import { useAdminUsers } from "../hooks/useAdmin"

const roleLabels: Record<number, string> = { 1: "Admin", 2: "Manager", 3: "Employee" }

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  })
}

export default function AdminUsersPage() {
  const { data: users, isLoading, error } = useAdminUsers()

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold text-text mb-1">Users</h1>
      <p className="text-sm text-text-muted mb-6">
        {users ? `${users.length} user${users.length !== 1 ? "s" : ""}` : "Loading..."}
      </p>

      {isLoading && <div className="text-sm text-text-muted py-12 text-center">Loading users...</div>}
      {error && <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-3">Failed to load users</div>}

      {users && users.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted text-xs uppercase tracking-wider">
                <th className="text-left py-3 pr-4 font-medium">Name</th>
                <th className="text-left py-3 pr-4 font-medium">Email</th>
                <th className="text-left py-3 pr-4 font-medium">Role</th>
                <th className="text-left py-3 pr-4 font-medium">Department</th>
                <th className="text-left py-3 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-border/50 hover:bg-bg-hover transition-colors">
                  <td className="py-3 pr-4 text-text font-medium">{u.name}</td>
                  <td className="py-3 pr-4 text-text-muted">{u.email}</td>
                  <td className="py-3 pr-4">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                      u.role_id === 1
                        ? "bg-accent/10 text-accent border-accent/20"
                        : u.role_id === 2
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-bg-surface text-text-muted border-border"
                    }`}>
                      {roleLabels[u.role_id] || u.role_name}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-text-muted">{u.department_name}</td>
                  <td className="py-3 text-text-muted whitespace-nowrap">{formatDate(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

import { useState } from "react"
import { useAdminUsers, useUpdateUser } from "../hooks/useAdmin"
import { useDepartments, useRoles } from "../hooks/useReferences"
import { useToast } from "../components/ui/Toast"
import type { User } from "../types"

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  })
}

function roleBadgeClass(roleName: string | null) {
  if (roleName === "Admin") return "bg-accent/10 text-accent border-accent/20"
  if (roleName === "Manager") return "bg-blue-500/10 text-blue-400 border-blue-500/20"
  return "bg-bg-surface text-text-muted border-border"
}

export default function AdminUsersPage() {
  const { data: users, isLoading, error } = useAdminUsers()
  const { data: departments } = useDepartments()
  const { data: roles } = useRoles()
  const update = useUpdateUser()
  const { toast } = useToast()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState<{ role_id: number; department_id: number | null }>({
    role_id: 3,
    department_id: null,
  })

  const startEdit = (u: User) => {
    setEditingId(u.id)
    setDraft({ role_id: u.role_id, department_id: u.department_id })
  }

  const saveEdit = async () => {
    if (editingId === null) return
    try {
      await update.mutateAsync({ id: editingId, ...draft })
      toast("User updated")
      setEditingId(null)
    } catch {
      toast("Failed to update user", "error")
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold text-text mb-1">Users</h1>
      <p className="text-sm text-text-muted mb-6">
        {users ? `${users.length} user${users.length !== 1 ? "s" : ""}` : "Loading..."}
      </p>

      {isLoading && <div className="text-sm text-text-muted py-12 text-center">Loading users...</div>}
      {error && <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-3">Failed to load users</div>}

      {users && users.length === 0 && (
        <div className="text-sm text-text-muted py-12 text-center">No users found.</div>
      )}

      {users && users.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted text-xs uppercase tracking-wider">
                <th className="text-left py-3 pr-4 font-medium">Name</th>
                <th className="text-left py-3 pr-4 font-medium">Email</th>
                <th className="text-left py-3 pr-4 font-medium">Role</th>
                <th className="text-left py-3 pr-4 font-medium">Department</th>
                <th className="text-left py-3 pr-4 font-medium">Joined</th>
                <th className="text-right py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const editing = editingId === u.id
                return (
                  <tr key={u.id} className="border-b border-border/50 hover:bg-bg-hover transition-colors">
                    <td className="py-3 pr-4 text-text font-medium">{u.name}</td>
                    <td className="py-3 pr-4 text-text-muted">{u.email}</td>
                    <td className="py-3 pr-4">
                      {editing ? (
                        <select
                          value={draft.role_id}
                          onChange={(e) => setDraft({ ...draft, role_id: Number(e.target.value) })}
                          className="bg-bg-base border border-border rounded-lg px-2 py-1 text-sm text-text focus:outline-none focus:border-accent"
                        >
                          {(roles || []).map((r) => (
                            <option key={r.id} value={r.id}>{r.name}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium border ${roleBadgeClass(u.role_name)}`}>
                          {u.role_name || "—"}
                        </span>
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      {editing ? (
                        <select
                          value={draft.department_id ?? ""}
                          onChange={(e) => setDraft({ ...draft, department_id: e.target.value ? Number(e.target.value) : null })}
                          className="bg-bg-base border border-border rounded-lg px-2 py-1 text-sm text-text focus:outline-none focus:border-accent"
                        >
                          <option value="">None</option>
                          {(departments || []).map((d) => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="text-text-muted">{u.department_name || "—"}</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-text-muted whitespace-nowrap">{formatDate(u.created_at)}</td>
                    <td className="py-3 text-right whitespace-nowrap">
                      {editing ? (
                        <>
                          <button
                            onClick={saveEdit}
                            disabled={update.isPending}
                            className="text-accent hover:text-accent-hover text-xs px-2 py-1 disabled:opacity-50"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="text-text-dim hover:text-text text-xs px-2 py-1"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => startEdit(u)}
                          className="text-accent hover:text-accent-hover text-xs px-2 py-1"
                        >
                          Edit
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
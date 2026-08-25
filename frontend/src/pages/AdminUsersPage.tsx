import { useState } from "react"
import { useAdminUsers, useUpdateUser, useCreateUser } from "@/hooks/useAdmin"
import { useDepartments, useRoles } from "@/hooks/useReferences"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import { Users, Loader2, UserPlus, ChevronLeft, ChevronRight } from "lucide-react"
import type { User } from "@/types"

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}
function roleVariant(roleName: string | null): "default" | "secondary" | "outline" {
  if (roleName === "Admin") return "default"
  if (roleName === "Manager") return "secondary"
  return "outline"
}

export default function AdminUsersPage() {
  const [page, setPage] = useState(0)
  const [limit, setLimit] = useState(10)
  const skip = page * limit
  const { data: users, isLoading, error } = useAdminUsers({ skip, limit })
  const { data: departments } = useDepartments()
  const { data: roles } = useRoles()
  const update = useUpdateUser()
  const create = useCreateUser()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState<{ name: string; role_id: number; department_id: number | null }>({ name: "", role_id: 3, department_id: null })
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({ name: "", email: "", password: "", department_id: 1, role_id: 3 })

  const startEdit = (u: User) => {
    setEditingId(u.id)
    setDraft({ name: u.name, role_id: u.role_id, department_id: u.department_id })
  }

  const saveEdit = async () => {
    if (editingId === null) return
    if (!draft.name.trim()) {
      toast.error("Name is required")
      return
    }
    try {
      await update.mutateAsync({ id: editingId, name: draft.name, role_id: draft.role_id, department_id: draft.department_id })
      toast.success("User updated")
      setEditingId(null)
    } catch {
      toast.error("Failed to update user")
    }
  }

  const handleCreate = async () => {
    if (!form.name || !form.email || !form.password) {
      toast.error("All fields are required")
      return
    }
    if (form.password.length < 8) {
      toast.error("Password must be at least 8 characters")
      return
    }
    try {
      await create.mutateAsync(form)
      toast.success("User created")
      setCreateOpen(false)
      setForm({ name: "", email: "", password: "", department_id: 1, role_id: 3 })
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to create user"
      toast.error(msg)
    }
  }

  const hasMore = users ? users.items.length < users.total : false

  return (
    <div className="mx-auto max-w-6xl p-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" /> Users
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {users ? `${users.total} total · page ${page + 1}` : "Loading..."} · Manage roles, departments, and create users
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <UserPlus className="h-4 w-4" /> Create user
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">All Users</CardTitle>
              <CardDescription>Only admins can modify users · Pagination enabled</CardDescription>
            </div>
            <Select value={String(limit)} onValueChange={(v) => { setLimit(Number(v)); setPage(0) }}>
              <SelectTrigger className="w-[110px] h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5">5 / page</SelectItem>
                <SelectItem value="10">10 / page</SelectItem>
                <SelectItem value="25">25 / page</SelectItem>
                <SelectItem value="50">50 / page</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading && (
            <div className="p-6 space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}
          {error && <div className="mx-6 my-4 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">Failed to load users</div>}
          {users && users.items.length === 0 && <div className="py-12 text-center text-sm text-muted-foreground">No users found.</div>}
          {users && users.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.items.map((u) => {
                      const editing = editingId === u.id
                      return (
                        <TableRow key={u.id}>
                          <TableCell className="font-medium min-w-[140px]">
                            {editing ? (
                              <Input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} className="h-8" />
                            ) : (
                              u.name
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">{u.email}</TableCell>
                          <TableCell>
                            {editing ? (
                              <Select value={String(draft.role_id)} onValueChange={(v) => setDraft({ ...draft, role_id: Number(v) })}>
                                <SelectTrigger className="w-[130px] h-8">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {(roles || []).map((r) => (
                                    <SelectItem key={r.id} value={String(r.id)}>{r.name}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            ) : (
                              <Badge variant={roleVariant(u.role_name)} className="capitalize">{u.role_name || "—"}</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {editing ? (
                              <Select
                                value={draft.department_id ? String(draft.department_id) : "none"}
                                onValueChange={(v) => setDraft({ ...draft, department_id: v === "none" ? null : Number(v) })}
                              >
                                <SelectTrigger className="w-[150px] h-8">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="none">None</SelectItem>
                                  {(departments || []).map((d) => (
                                    <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            ) : (
                              <span className="text-sm text-muted-foreground">{u.department_name || "—"}</span>
                            )}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground whitespace-nowrap">{formatDate(u.created_at)}</TableCell>
                          <TableCell className="text-right">
                            {editing ? (
                              <div className="flex justify-end gap-1">
                                <Button size="sm" onClick={saveEdit} disabled={update.isPending} className="h-7">
                                  {update.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Save"}
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => setEditingId(null)} className="h-7">
                                  Cancel
                                </Button>
                              </div>
                            ) : (
                              <Button size="sm" variant="ghost" onClick={() => startEdit(u)} className="h-7">
                                Edit
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
              <div className="flex items-center justify-between border-t px-4 py-3">
                <span className="text-xs text-muted-foreground">Page {page + 1}</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))} className="h-8 gap-1">
                    <ChevronLeft className="h-4 w-4" /> Prev
                  </Button>
                  <Button variant="outline" size="sm" disabled={!hasMore} onClick={() => setPage((p) => p + 1)} className="h-8 gap-1">
                    Next <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create user</DialogTitle>
            <DialogDescription>Admin can create users with any role.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="c-name">Name</Label>
              <Input id="c-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Jane Doe" />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="c-email">Email</Label>
              <Input id="c-email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="jane@company.com" />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="c-pass">Password</Label>
              <Input id="c-pass" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Min 6 chars" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-2">
                <Label>Department</Label>
                <Select value={String(form.department_id)} onValueChange={(v) => setForm({ ...form, department_id: Number(v) })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(departments || []).map((d) => (
                      <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>Role</Label>
                <Select value={String(form.role_id)} onValueChange={(v) => setForm({ ...form, role_id: Number(v) })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(roles || []).map((r) => (
                      <SelectItem key={r.id} value={String(r.id)}>{r.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={create.isPending} className="gap-2">
              {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />} Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

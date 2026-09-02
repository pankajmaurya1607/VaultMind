import { useState } from "react"
import { useDepartments, useRoles, useCreateDepartment, useCreateRole } from "@/hooks/useReferences"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Building2, Shield, Plus, Loader2 } from "lucide-react"
import { toast } from "sonner"

export default function AdminDepartmentsPage() {
  const { data: deps, isLoading: depsLoading, error: depsError } = useDepartments()
  const { data: roles, isLoading: rolesLoading } = useRoles()
  const createDept = useCreateDepartment()
  const createRole = useCreateRole()
  const [newDept, setNewDept] = useState("")
  const [newRole, setNewRole] = useState("")

  const handleCreateDept = async () => {
    const name = newDept.trim()
    if (!name) return
    try {
      await createDept.mutateAsync(name)
      toast.success(`Department "${name}" created`)
      setNewDept("")
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || (err as Error).message || "Failed to create department"
      toast.error(msg)
    }
  }

  const handleCreateRole = async () => {
    const name = newRole.trim()
    if (!name) return
    try {
      await createRole.mutateAsync(name)
      toast.success(`Role "${name}" created`)
      setNewRole("")
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || (err as Error).message || "Failed to create role"
      toast.error(msg)
    }
  }

  return (
    <div className="mx-auto max-w-5xl p-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Building2 className="h-6 w-6 text-primary" /> Departments & Roles
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Manage organization structure — defaults seeded, add new as needed</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-4 w-4" /> Departments</CardTitle>
            <CardDescription>{deps ? `${deps.length} departments` : "Loading..."} — default: Finance, HR, Engineering, Sales, Marketing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {depsLoading && <Skeleton className="h-20 w-full" />}
            {depsError && <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">Failed to load departments</div>}
            {deps && (
              <div className="flex flex-wrap gap-2">
                {deps.map((d) => (
                  <Badge key={d.id} variant="secondary" className="px-3 py-1.5 text-sm">
                    #{d.id} {d.name}
                  </Badge>
                ))}
              </div>
            )}
            <div className="flex gap-2 pt-2 border-t">
              <Input placeholder="New department (e.g. Legal)" value={newDept} onChange={(e) => setNewDept(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleCreateDept()} maxLength={50} />
              <Button onClick={handleCreateDept} disabled={createDept.isPending || !newDept.trim()} size="sm" className="gap-1 shrink-0">
                {createDept.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />} Add
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Defaults kept: 5 seeded. New departments appear in registration dropdown instantly.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base"><Shield className="h-4 w-4" /> Roles</CardTitle>
            <CardDescription>{roles ? `${roles.length} roles` : "Loading..."} — default: Admin, Manager, Employee</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {rolesLoading && <Skeleton className="h-20 w-full" />}
            {roles && (
              <div className="flex flex-wrap gap-2">
                {roles.map((r) => (
                  <Badge key={r.id} variant={r.name === "Admin" ? "default" : r.name === "Manager" ? "secondary" : "outline"} className="capitalize px-3 py-1.5">
                    #{r.id} {r.name}
                  </Badge>
                ))}
              </div>
            )}
            <div className="flex gap-2 pt-2 border-t">
              <Input placeholder="New role (e.g. Auditor)" value={newRole} onChange={(e) => setNewRole(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleCreateRole()} maxLength={30} />
              <Button onClick={handleCreateRole} disabled={createRole.isPending || !newRole.trim()} size="sm" className="gap-1 shrink-0">
                {createRole.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />} Add
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Defaults kept: 3 seeded (Admin/Manager/Employee). New roles usable in Admin → Users.</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6 bg-muted/30">
        <CardContent className="pt-6 text-sm text-muted-foreground">
          <strong>Note:</strong> Registration always creates <code className="px-1 py-0.5 rounded bg-background text-xs">Employee</code> — admin changes role via <code className="px-1 py-0.5 rounded bg-background text-xs">Admin → Users → Edit</code>. Departments are public for signup; roles are admin-only.
        </CardContent>
      </Card>
    </div>
  )
}

import { useDepartments, useRoles } from "@/hooks/useReferences"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Building2, Shield } from "lucide-react"

export default function AdminDepartmentsPage() {
  const { data: deps, isLoading: depsLoading, error: depsError } = useDepartments()
  const { data: roles, isLoading: rolesLoading } = useRoles()

  return (
    <div className="mx-auto max-w-5xl p-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Building2 className="h-6 w-6 text-primary" /> Departments & Roles
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Organization structure — read-only (backend has no CRUD endpoints)</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-4 w-4" /> Departments</CardTitle>
            <CardDescription>{deps ? `${deps.length} departments` : "Loading..."}</CardDescription>
          </CardHeader>
          <CardContent>
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
            <p className="mt-4 text-xs text-muted-foreground">Seed: Finance, HR, Engineering, Sales, Marketing. Manage via DB seed; no POST/PUT API available.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base"><Shield className="h-4 w-4" /> Roles</CardTitle>
            <CardDescription>{roles ? `${roles.length} roles` : "Loading..."}</CardDescription>
          </CardHeader>
          <CardContent>
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
            <p className="mt-4 text-xs text-muted-foreground">Admin = full access, Manager = dept+own (currently same as Employee), Employee = own docs.</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6 border-dashed">
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">To enable CRUD, backend needs <code className="px-1 py-0.5 rounded bg-muted text-xs">POST/PUT/DELETE /departments</code> endpoints. Frontend is ready to consume them — just add hooks.</p>
        </CardContent>
      </Card>
    </div>
  )
}

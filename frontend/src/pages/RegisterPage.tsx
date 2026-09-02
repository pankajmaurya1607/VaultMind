import { Link, useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useAuth } from "@/context/AuthContext"
import { useDepartments } from "@/hooks/useReferences"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

const registerSchema = z.object({
  name: z.string().min(1, "Name is required").min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address").min(1, "Email is required"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  department_id: z.number().min(1, "Department is required"),
})

type RegisterValues = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const { data: departments, isLoading: departmentsLoading, error: departmentsError } = useDepartments()

  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "", department_id: 1 },
  })

  // auto-select first department when loaded (fixes empty default when seed not id 1)
  if (departments && departments.length > 0 && form.getValues("department_id") === 1 && !departments.find((d) => d.id === 1)) {
    // no-op, keep 1 - server will validate
  }

  const onSubmit = async (values: RegisterValues) => {
    try {
      await register(values)
      toast.success("Account created")
      navigate("/dashboard")
    } catch (err: unknown) {
      let msg = "Registration failed. Please try again."
      const errorResponse =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
      if (errorResponse?.detail) {
        const detail = errorResponse.detail
        if (detail.includes("already registered")) {
          msg = "An account with this email already exists."
        } else {
          msg = detail
        }
      }
      toast.error(msg)
      form.setError("root", { message: msg })
    }
  }

  const rootError = form.formState.errors.root?.message

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-background py-12">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/5" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />

      <div className="relative w-full max-w-sm px-6">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold tracking-tight">VaultMind</h1>
          <p className="text-sm text-muted-foreground mt-1">Create your account</p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg">Create account</CardTitle>
            <CardDescription>Enter your details to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
                {rootError && (
                  <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-md px-4 py-2.5" role="alert">
                    {rootError}
                  </div>
                )}

                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Jane Doe" autoComplete="name" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input placeholder="you@company.com" type="email" autoComplete="email" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Password</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Min. 6 characters"
                          type="password"
                          autoComplete="new-password"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="department_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Department</FormLabel>
                      <Select
                        value={String(field.value)}
                        onValueChange={(v) => field.onChange(Number(v))}
                        disabled={departmentsLoading || !!departmentsError || !departments || departments.length === 0}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder={departmentsLoading ? "Loading departments..." : departmentsError ? "Failed to load" : departments && departments.length === 0 ? "No departments" : "Select department"} />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {(departments || []).map((d) => (
                            <SelectItem key={d.id} value={String(d.id)}>
                              {d.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {departmentsError && <p className="text-xs text-destructive mt-1">Could not load departments. Please refresh.</p>}
                      <p className="text-xs text-muted-foreground mt-1">Role will be Employee — admin can change it later.</p>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating account...
                    </>
                  ) : (
                    "Create account"
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
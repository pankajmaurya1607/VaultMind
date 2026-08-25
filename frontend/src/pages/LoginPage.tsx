import { Link, useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useAuth } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

const loginSchema = z.object({
  email: z.string().email("Invalid email address").min(1, "Email is required"),
  password: z.string().min(1, "Password is required"),
})

type LoginValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  })

  const onSubmit = async (values: LoginValues) => {
    try {
      await login(values)
      toast.success("Welcome back")
      navigate("/dashboard")
    } catch (err: unknown) {
      let msg = "Login failed. Please try again."
      const errorResponse =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
      if (errorResponse?.detail) {
        const detail = errorResponse.detail
        if (detail.includes("Invalid credentials")) {
          msg = "Wrong email or password. Please check and try again."
        } else if (detail.includes("already registered")) {
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
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-background">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/5" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />

      <div className="relative w-full max-w-sm px-6">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold tracking-tight">VaultMind</h1>
          <p className="text-sm text-muted-foreground mt-1">Sign in to your account</p>
        </div>

        <Card className="border-border bg-card">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg">Sign in</CardTitle>
            <CardDescription>Enter your credentials to continue</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
                {rootError && (
                  <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-md px-4 py-2.5 animate-fade-in" role="alert">
                    {rootError}
                  </div>
                )}

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel htmlFor="email" className="mb-1">Email</FormLabel>
                      <FormControl>
                        <Input
                          id="email"
                          placeholder="you@company.com"
                          autoComplete="email"
                          type="email"
                          {...field}
                          aria-label="Email address"
                        />
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
                      <FormLabel htmlFor="password" className="mb-1">Password</FormLabel>
                      <FormControl>
                        <Input
                          id="password"
                          placeholder="Enter your password"
                          type="password"
                          autoComplete="current-password"
                          {...field}
                          aria-label="Password"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    "Sign in"
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-muted-foreground mt-4">
          Don&apos;t have an account?{" "}
          <Link to="/register" className="text-primary hover:text-primary/80 transition-colors font-medium">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}

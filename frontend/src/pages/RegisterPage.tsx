import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { useDepartments } from "../hooks/useReferences"
import type { RegisterBody } from "../types"

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const { data: departments, isLoading: departmentsLoading } = useDepartments()
  const [form, setForm] = useState<RegisterBody>({
    name: "",
    email: "",
    password: "",
    department_id: 1,
  })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    if (!form.name || !form.email || !form.password) {
      setError("All fields are required")
      return
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }
    setLoading(true)
    try {
      await register(form)
      navigate("/dashboard")
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Registration failed. Please try again."
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-bg-base">
      <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-bg-base to-accent/5" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />

      <div className="relative w-full max-w-sm px-6">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold text-text">VaultMind</h1>
          <p className="text-text-muted mt-1 text-sm">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-bg-surface border border-border rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-2.5 animate-fade-in">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="block text-sm font-medium text-text-muted mb-1.5">
              Name
            </label>
            <input
              id="name"
              type="text"
              autoComplete="name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-bg-base border border-border rounded-lg px-3.5 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
              placeholder="Jane Doe"
            />
          </div>

          <div>
            <label htmlFor="reg-email" className="block text-sm font-medium text-text-muted mb-1.5">
              Email
            </label>
            <input
              id="reg-email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full bg-bg-base border border-border rounded-lg px-3.5 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label htmlFor="reg-password" className="block text-sm font-medium text-text-muted mb-1.5">
              Password
            </label>
            <input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full bg-bg-base border border-border rounded-lg px-3.5 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
              placeholder="Min. 6 characters"
            />
          </div>

          <div>
            <label htmlFor="department" className="block text-sm font-medium text-text-muted mb-1.5">
              Department
            </label>
            <select
              id="department"
              value={form.department_id}
              onChange={(e) => setForm({ ...form, department_id: Number(e.target.value) })}
              className="w-full bg-bg-base border border-border rounded-lg px-3.5 py-2.5 text-text text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors appearance-none cursor-pointer"
            >
              {departmentsLoading ? (
                <option>Loading departments...</option>
              ) : (
                (departments || []).map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))
              )}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating account...
              </>
            ) : (
              "Create account"
            )}
          </button>
        </form>

        <p className="text-center text-sm text-text-muted mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:text-accent-hover transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

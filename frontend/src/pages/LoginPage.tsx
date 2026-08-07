import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import type { LoginBody } from "../types"

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<LoginBody>({ email: "", password: "" })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    if (!form.email || !form.password) {
      setError("Email and password are required")
      return
    }
    setLoading(true)
    try {
      await login(form)
      navigate("/dashboard")
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Login failed. Please try again."
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
          <p className="text-text-muted mt-1 text-sm">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-bg-surface border border-border rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-2.5 animate-fade-in">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-text-muted mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full bg-bg-base border border-border rounded-lg px-3.5 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text-muted mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full bg-bg-base border border-border rounded-lg px-3.5 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Signing in...
              </>
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <p className="text-center text-sm text-text-muted mt-4">
          Don't have an account?{" "}
          <Link to="/register" className="text-accent hover:text-accent-hover transition-colors">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}

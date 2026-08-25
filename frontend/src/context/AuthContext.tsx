import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { useQueryClient } from "@tanstack/react-query"
import api from "../lib/api"
import type { User, LoginBody, RegisterBody } from "../types"

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (body: LoginBody) => Promise<void>
  register: (body: RegisterBody) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const queryClient = useQueryClient()

  useEffect(() => {
    // Auth lives in HttpOnly cookies - probe the server to restore the session.
    api
      .get<User>("/users/me")
      .then((res) => setUser(res.data))
      .catch(() => setUser(null)) // logged out is a normal state, not an error
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const onExpired = () => {
      setUser(null)
      queryClient.clear() // never leak the previous user's cached data
    }
    window.addEventListener("auth:expired", onExpired)
    return () => window.removeEventListener("auth:expired", onExpired)
  }, [queryClient])

  const login = async (body: LoginBody) => {
    await api.post("/auth/login", body)
    const userRes = await api.get<User>("/users/me")
    setUser(userRes.data)
  }

  const register = async (body: RegisterBody) => {
    await api.post("/auth/register", body)
    const userRes = await api.get<User>("/users/me")
    setUser(userRes.data)
  }

  const logout = async () => {
    try {
      await api.post("/auth/logout")
    } catch {
      // ignore - clear local state regardless
    }
    setUser(null)
    queryClient.clear()
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}

export function isAdmin(user: User | null) {
  return user?.role_name === "Admin"
}

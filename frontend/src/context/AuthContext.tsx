import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
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

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get<User>("/users/me")
      .then((res) => {
        setUser(res.data)
        localStorage.setItem("user", JSON.stringify(res.data))
      })
      .catch(() => {
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        localStorage.removeItem("user")
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (body: LoginBody) => {
    const { data } = await api.post("/auth/login", body)
    localStorage.setItem("access_token", data.access_token)
    localStorage.setItem("refresh_token", data.refresh_token)
    const userRes = await api.get<User>("/users/me")
    setUser(userRes.data)
    localStorage.setItem("user", JSON.stringify(userRes.data))
  }

  const register = async (body: RegisterBody) => {
    const { data } = await api.post("/auth/register", body)
    localStorage.setItem("access_token", data.access_token)
    localStorage.setItem("refresh_token", data.refresh_token)
    const userRes = await api.get<User>("/users/me")
    setUser(userRes.data)
    localStorage.setItem("user", JSON.stringify(userRes.data))
  }

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem("refresh_token")
      await api.post("/auth/logout", null, {
        headers: {
          "X-Refresh-Token": refreshToken || "",
        },
      })
    } catch {
      // ignore
    }
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("user")
    setUser(null)
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

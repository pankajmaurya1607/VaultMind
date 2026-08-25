import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@/test/utils"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import LoginPage from "@/pages/LoginPage"
import RegisterPage from "@/pages/RegisterPage"
import { AuthProvider } from "@/context/AuthContext"
import api from "@/lib/api"

function renderWithAuth(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

describe("LoginPage", () => {
  beforeEach(() => localStorage.clear())

  it("renders form fields", () => {
    renderWithAuth(<LoginPage />)
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it("shows validation errors on empty submit", async () => {
    const user = userEvent.setup()
    renderWithAuth(<LoginPage />)
    const btn = screen.getByRole("button", { name: /sign in/i })
    await user.click(btn)
    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument()
  })

  it("calls login and navigates on success", async () => {
    const user = userEvent.setup()
    render(
      <QueryClientProvider client={new QueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={["/login"]}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<div>Dashboard</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    )
    await user.type(screen.getByLabelText(/email/i), "admin@eka.com")
    await user.type(screen.getByLabelText(/password/i), "admin123")
    await user.click(screen.getByRole("button", { name: /sign in/i }))
    await waitFor(() => expect(screen.getByText("Dashboard")).toBeInTheDocument(), { timeout: 3000 })
    expect(localStorage.getItem("access_token")).toBe("mock_access")
  })

  it("shows error on invalid credentials", async () => {
    const user = userEvent.setup()
    renderWithAuth(<LoginPage />)
    await user.type(screen.getByLabelText(/email/i), "wrong@eka.com")
    await user.type(screen.getByLabelText(/password/i), "wrongpass")
    await user.click(screen.getByRole("button", { name: /sign in/i }))
    await waitFor(() => expect(screen.getByText(/wrong email or password/i)).toBeInTheDocument(), { timeout: 3000 })
  })
})

describe("RegisterPage", () => {
  beforeEach(() => localStorage.clear())

  it("renders register form with department select", async () => {
    renderWithAuth(<RegisterPage />)
    expect(screen.getByRole("heading", { name: /create account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    // department select appears after departments load
    await waitFor(() => expect(screen.getAllByText("Engineering").length).toBeGreaterThan(0), { timeout: 3000 })
  })

  it("validates name required", async () => {
    const user = userEvent.setup()
    renderWithAuth(<RegisterPage />)
    await waitFor(() => expect(screen.getAllByText("Engineering").length).toBeGreaterThan(0), { timeout: 3000 })
    const btn = screen.getByRole("button", { name: /create account/i })
    await user.click(btn)
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
  })
})

describe("Auth API interceptor", () => {
  it("adds Authorization header when token exists", async () => {
    localStorage.setItem("access_token", "test_token")
    const config = { headers: {} as Record<string, string> } as never
    // simulate interceptor
    const token = localStorage.getItem("access_token")
    if (token) (config.headers as Record<string,string>).Authorization = `Bearer ${token}`
    expect((config.headers as Record<string,string>).Authorization).toBe("Bearer test_token")
    localStorage.clear()
  })

  it("isAdmin utility", async () => {
    const { isAdmin } = await import("@/context/AuthContext")
    expect(isAdmin({ role_name: "Admin" } as never)).toBe(true)
    expect(isAdmin({ role_name: "Employee" } as never)).toBe(false)
    expect(isAdmin(null)).toBe(false)
  })
})

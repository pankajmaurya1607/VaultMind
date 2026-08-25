import { describe, it, expect } from "vitest"
import { render, screen, waitFor } from "@/test/utils"
import AdminMetricsPage from "@/pages/AdminMetricsPage"
import AdminUsersPage from "@/pages/AdminUsersPage"
import AdminAuditPage from "@/pages/AdminAuditPage"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

function renderWithQC(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe("AdminMetricsPage", () => {
  it("renders metrics cards", async () => {
    renderWithQC(<AdminMetricsPage />)
    await waitFor(() => expect(screen.getByText("42")).toBeInTheDocument(), { timeout: 3000 })
    expect(screen.getByText(/system metrics/i)).toBeInTheDocument()
    expect(screen.getByText("Documents")).toBeInTheDocument()
    expect(screen.getByText("Users")).toBeInTheDocument()
    expect(screen.getByText(/total tokens/i)).toBeInTheDocument()
  })

  it("shows documents by status", async () => {
    renderWithQC(<AdminMetricsPage />)
    await waitFor(() => expect(screen.getByText("ready")).toBeInTheDocument(), { timeout: 3000 })
  })
})

describe("AdminUsersPage", () => {
  it("renders users table", async () => {
    renderWithQC(<AdminUsersPage />)
    await waitFor(() => expect(screen.getByText("Admin User")).toBeInTheDocument(), { timeout: 3000 })
    expect(screen.getByText("jane@company.com")).toBeInTheDocument()
    expect(screen.getAllByText("Engineering").length).toBeGreaterThan(0)
  })

  it("allows editing a user", async () => {
    const { container } = renderWithQC(<AdminUsersPage />)
    await waitFor(() => expect(screen.getByText("Admin User")).toBeInTheDocument(), { timeout: 3000 })
    const editBtn = screen.getAllByText("Edit")[0]
    const user = (await import("@testing-library/user-event")).default
    const u = user.setup()
    await u.click(editBtn)
    expect(screen.getByText("Save")).toBeInTheDocument()
    expect(screen.getByText("Cancel")).toBeInTheDocument()
  })
})

describe("AdminAuditPage", () => {
  it("renders audit logs", async () => {
    renderWithQC(<AdminAuditPage />)
    await waitFor(() => expect(screen.getByText("admin@eka.com")).toBeInTheDocument(), { timeout: 3000 })
    expect(screen.getByText("login")).toBeInTheDocument()
    expect(screen.getByText("Success")).toBeInTheDocument()
  })
})

import { describe, it, expect, vi } from "vitest"
import { render, screen, waitFor } from "@/test/utils"
import userEvent from "@testing-library/user-event"
import DocumentsPage from "@/pages/DocumentsPage"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { AuthProvider } from "@/context/AuthContext"

vi.mock("@/context/AuthContext", async () => {
  const actual = await vi.importActual("@/context/AuthContext") as never
  return {
    ...(actual as object),
    useAuth: () => ({ user: { id: 1, name: "Admin", role_name: "Admin", email: "admin@eka.com" }, loading: false, login: vi.fn(), register: vi.fn(), logout: vi.fn() }),
    isAdmin: () => true,
  }
})

function renderDocs() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuthProvider>
          <DocumentsPage />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

// Since we mock AuthContext above, but provider still needed, simplify direct render
function renderDocsSimple() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe("DocumentsPage", () => {
  it("renders documents table after loading", async () => {
    renderDocsSimple()
    expect(screen.getByText(/documents/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText("handbook.pdf")).toBeInTheDocument(), { timeout: 3000 })
    expect(screen.getByText("report.csv")).toBeInTheDocument()
    expect(screen.getByText("ready")).toBeInTheDocument()
  })

  it("filters by filename", async () => {
    const user = userEvent.setup()
    renderDocsSimple()
    await waitFor(() => expect(screen.getByText("handbook.pdf")).toBeInTheDocument())
    const input = screen.getByPlaceholderText(/filter by filename/i)
    await user.type(input, "handbook")
    await waitFor(() => expect(screen.getByText("handbook.pdf")).toBeInTheDocument())
    expect(screen.queryByText("report.csv")).not.toBeInTheDocument()
    await user.clear(input)
    await user.type(input, "nonexistent")
    await waitFor(() => expect(screen.getByText(/no documents match/i)).toBeInTheDocument())
  })

  it("opens detail dialog on row click", async () => {
    const user = userEvent.setup()
    renderDocsSimple()
    await waitFor(() => expect(screen.getByText("handbook.pdf")).toBeInTheDocument())
    await user.click(screen.getByText("handbook.pdf"))
    // dialog shows filename as title and contains status/detail
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument(), { timeout: 3000 })
    expect(screen.getByText(/detailed info/i)).toBeInTheDocument()
  })

  it("opens upload dialog", async () => {
    const user = userEvent.setup()
    renderDocsSimple()
    await waitFor(() => expect(screen.getByText("handbook.pdf")).toBeInTheDocument())
    await user.click(screen.getByRole("button", { name: /upload/i }))
    await waitFor(() => expect(screen.getByText("Upload Document")).toBeInTheDocument(), { timeout: 3000 })
  })
})

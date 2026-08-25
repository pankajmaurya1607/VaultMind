import { describe, it, expect, vi } from "vitest"
import { render, screen, waitFor } from "@/test/utils"
import userEvent from "@testing-library/user-event"
import ChatPage from "@/pages/ChatPage"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"

function renderChat() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ChatPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe("ChatPage", () => {
  it("renders new chat empty state", async () => {
    renderChat()
    // Empty state title
    await waitFor(() => expect(screen.getByText(/ask anything/i)).toBeInTheDocument(), { timeout: 3000 })
    expect(screen.getByText(/ask questions about your documents/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument()
  })

  it("shows sessions list", async () => {
    renderChat()
    await waitFor(() => expect(screen.getAllByText("First conversation").length).toBeGreaterThan(0), { timeout: 3000 })
    expect(screen.getByText("New Chat").textContent).toContain("New Chat")
  })

  it("sends message and shows answer", async () => {
    const user = userEvent.setup()
    renderChat()
    await waitFor(() => expect(screen.getByText(/ask anything/i)).toBeInTheDocument(), { timeout: 3000 })
    const input = screen.getByPlaceholderText(/ask a question/i)
    await user.type(input, "What is onboarding?")
    await user.click(screen.getByRole("button", { name: /^send$/i }))
    await waitFor(() => expect(screen.getByText(/mock answer for/i)).toBeInTheDocument(), { timeout: 4000 })
    expect(screen.getAllByText(/confidence/i).length).toBeGreaterThan(0)
  })

  it("handles enter key to send", async () => {
    const user = userEvent.setup()
    renderChat()
    await waitFor(() => expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument())
    const input = screen.getByPlaceholderText(/ask a question/i)
    await user.type(input, "Hello{enter}")
    await waitFor(() => expect(screen.getByText(/mock answer for/i)).toBeInTheDocument(), { timeout: 4000 })
  })

  it("shows suggestion chips", async () => {
    renderChat()
    await waitFor(() => expect(screen.getByText(/what are the company leave policies/i)).toBeInTheDocument(), { timeout: 3000 })
    const user = userEvent.setup()
    await user.click(screen.getByText(/what are the company leave policies/i))
    expect(screen.getByDisplayValue("What are the company leave policies?")).toBeInTheDocument()
  })
})

import { test, expect } from "@playwright/test"

async function mockAuthAndChat(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, name: "User", email: "user@company.com", department_id: 1, department_name: "Engineering", role_id: 3, role_name: "Employee", created_at: new Date().toISOString() }),
    })
  })
  await page.route("**/api/v1/chat/history", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([{ id: 1, title: "First conversation", created_at: new Date().toISOString(), message_count: 2 }]),
    })
  })
  await page.route("**/api/v1/chat/history/*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        { id: 1, role: "user", content: "Hello", sources: null, confidence_score: null, created_at: new Date().toISOString() },
        { id: 2, role: "assistant", content: "Hi there! How can I help?", sources: [], confidence_score: 0.9, created_at: new Date().toISOString() },
      ]),
    })
  })
  await page.route("**/api/v1/chat", async (route) => {
    const body = await route.request().postDataJSON() as { question: string; session_id: number | null }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: 1,
        answer: `Mock answer for: ${body.question}`,
        sources: [{ document_id: 1, filename: "handbook.pdf", chunk_index: 0, text: "Source excerpt", score: 0.88 }],
        confidence_score: 0.87,
        tokens_used: 42,
        latency_ms: 123,
      }),
    })
  })
}

test.describe("Chat", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthAndChat(page)
  })

  test("new chat empty state", async ({ page }) => {
    await page.goto("/chat")
    await expect(page.getByText(/ask anything/i)).toBeVisible()
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible()
    await expect(page.getByText("First conversation").first()).toBeVisible()
  })

  test("send message and get answer", async ({ page }) => {
    await page.goto("/chat")
    await expect(page.getByText(/ask anything/i)).toBeVisible()
    await page.getByPlaceholder(/ask a question/i).fill("What is onboarding?")
    await page.getByRole("button", { name: /^send$/i }).click()
    await expect(page.getByText(/mock answer for: what is onboarding/i)).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/confidence/i).first()).toBeVisible()
  })

  test("suggestion click fills input", async ({ page }) => {
    await page.goto("/chat")
    await expect(page.getByText(/what are the company leave policies/i)).toBeVisible()
    await page.getByText(/what are the company leave policies/i).click()
    await expect(page.getByPlaceholder(/ask a question/i)).toHaveValue("What are the company leave policies?")
  })

  test("switch to existing session shows history", async ({ page }) => {
    await page.goto("/chat")
    await page.getByText("First conversation").first().click()
    await expect(page.getByText("Hello")).toBeVisible({ timeout: 5000 })
    await expect(page.getByText("Hi there!")).toBeVisible()
  })
})

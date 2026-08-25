import { test, expect } from "@playwright/test"

async function mockAuth(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, name: "User", email: "user@company.com", department_id: 1, department_name: "Engineering", role_id: 3, role_name: "Employee", created_at: new Date().toISOString() }),
    })
  })
  await page.route("**/api/v1/search", async (route) => {
    const body = (await route.request().postDataJSON()) as { query: string } | null
    const q = body?.query || ""
    if (!q.trim()) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ results: [], total: 0 }) })
      return
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          { document_id: 1, filename: "handbook.pdf", chunk_index: 2, text: `Relevant content for "${q}" about onboarding and policies. Extra text to make it longer than 220 characters so highlight works and we can test expand behavior. `.repeat(2), score: 0.92, metadata: {} },
        ],
        total: 1,
      }),
    })
  })
}

test.describe("Search", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock_access")
      localStorage.setItem("refresh_token", "mock_refresh")
    })
    await mockAuth(page)
  })

  test("search flow: input, submit, results, highlight", async ({ page }) => {
    await page.goto("/search")
    await expect(page.getByRole("heading", { name: /search/i })).toBeVisible()
    const input = page.getByPlaceholder(/search your knowledge/i)
    await expect(input).toBeVisible()
    await input.fill("onboarding")
    await page.getByRole("button", { name: /^search$/i }).click()
    await expect(page.getByText("handbook.pdf")).toBeVisible()
    await expect(page.getByText(/1 result/i)).toBeVisible()
    const mark = page.locator("mark").first()
    await expect(mark).toBeVisible()
    await expect(mark).toContainText("onboarding", { ignoreCase: true })
  })

  test("search via URL query param", async ({ page }) => {
    await page.goto("/search?q=onboarding")
    await expect(page.getByText("handbook.pdf")).toBeVisible({ timeout: 5000 })
    await expect(page.getByPlaceholder(/search your knowledge/i)).toHaveValue("onboarding")
  })

  test("empty state when no query", async ({ page }) => {
    await page.goto("/search")
    await expect(page.getByText(/enter a query/i)).toBeVisible()
  })
})

import { test, expect } from "@playwright/test"
import AxeBuilder from "@axe-core/playwright"

async function mockAuth(page: import("@playwright/test").Page, role: "Admin" | "Employee" = "Admin") {
  // Cookie-based auth: AuthContext probes /users/me to restore the session.
  await page.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, name: "Test User", email: "test@eka.com", department_id: 1, department_name: "Engineering", role_id: role === "Admin" ? 1 : 3, role_name: role, created_at: new Date().toISOString() }),
    })
  })
  await page.route("**/api/v1/auth/refresh", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ access_token: "mock", refresh_token: "mock", token_type: "bearer" }) })
  })
  await page.route("**/api/v1/departments", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Engineering" }]) })
  })
  await page.route("**/api/v1/departments/roles", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Admin" }, { id: 3, name: "Employee" }]) })
  })
  const emptyPage = { items: [], total: 0, skip: 0, limit: 100 }
  await page.route("**/api/v1/documents*", async (route) => {
    if (route.request().method() === "GET" && !route.request().url().includes("/documents/")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(emptyPage) })
    } else {
      await route.continue()
    }
  })
  await page.route("**/api/v1/chat/history", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) })
  })
  await page.route("**/api/v1/admin/metrics", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ total_documents: 0, total_users: 1, total_chat_sessions: 0, documents_by_status: {}, total_tokens_used: 0, avg_chat_latency_ms: 0, avg_search_latency_ms: 0, error_count: 0 }) })
  })
  await page.route("**/api/v1/admin/audit**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(emptyPage) })
  })
  await page.route("**/api/v1/users*", async (route) => {
    if (route.request().url().includes("/users/me")) { await route.continue(); return }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(emptyPage) })
  })
}

test.describe("Accessibility (axe)", () => {
  test("landing page has no serious violations", async ({ page }) => {
    await page.goto("/")
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze()
    const filtered = results.violations.filter((v) => v.impact === "critical" || v.impact === "serious")
    expect(filtered).toEqual([])
  })

  test("login page has no critical violations", async ({ page }) => {
    await page.goto("/login")
    const results = await new AxeBuilder({ page }).analyze()
    const filtered = results.violations.filter((v) => v.impact === "critical")
    expect(filtered).toEqual([])
  })

  test("dashboard (authenticated) has no critical violations", async ({ page }) => {
    await mockAuth(page, "Employee")
    await page.goto("/dashboard")
    await expect(page.getByText(/welcome/i)).toBeVisible()
    const results = await new AxeBuilder({ page }).analyze()
    const filtered = results.violations.filter((v) => v.impact === "critical")
    expect(filtered).toEqual([])
  })

  test("documents page has no critical violations", async ({ page }) => {
    await mockAuth(page)
    await page.goto("/documents")
    await expect(page.getByText("Documents").first()).toBeVisible()
    const results = await new AxeBuilder({ page }).analyze()
    const filtered = results.violations.filter((v) => v.impact === "critical")
    expect(filtered).toEqual([])
  })
})

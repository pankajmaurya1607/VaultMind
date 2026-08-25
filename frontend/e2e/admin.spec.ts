import { test, expect } from "@playwright/test"

async function mockAdmin(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, name: "Admin User", email: "admin@eka.com", department_id: 1, department_name: "Engineering", role_id: 1, role_name: "Admin", created_at: new Date().toISOString() }),
    })
  })
  await page.route("**/api/v1/users*", async (route) => {
    const url = route.request().url()
    // let /users/me be handled by earlier handler
    if (url.includes("/users/me") || url.includes("/users/") && route.request().method() === "PATCH") {
      await route.continue()
      return
    }
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: 1, name: "Admin User", email: "admin@eka.com", department_id: 1, department_name: "Engineering", role_id: 1, role_name: "Admin", created_at: new Date().toISOString() },
          { id: 2, name: "Jane Doe", email: "jane@company.com", department_id: 1, department_name: "Engineering", role_id: 3, role_name: "Employee", created_at: new Date().toISOString() },
        ]),
      })
    } else {
      await route.continue()
    }
  })
  await page.route("**/api/v1/departments", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Engineering" }, { id: 2, name: "Marketing" }]) })
  })
  await page.route("**/api/v1/departments/roles", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Admin" }, { id: 2, name: "Manager" }, { id: 3, name: "Employee" }]) })
  })
  await page.route("**/api/v1/admin/metrics", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        total_documents: 42,
        total_users: 10,
        total_chat_sessions: 5,
        documents_by_status: { ready: 30, pending: 5 },
        total_tokens_used: 123456,
        avg_chat_latency_ms: 234,
        avg_search_latency_ms: 45,
        error_count: 1,
      }),
    })
  })
  await page.route("**/api/v1/admin/audit**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([{ id: 1, user_email: "admin@eka.com", action: "login", resource: "auth", details: null, ip_address: "127.0.0.1", success: 1, created_at: new Date().toISOString() }]),
    })
  })
}

test.describe("Admin pages", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock_access")
      localStorage.setItem("refresh_token", "mock_refresh")
    })
    await mockAdmin(page)
  })

  test("metrics page shows stats", async ({ page }) => {
    await page.goto("/admin/metrics")
    await expect(page.getByRole("heading", { name: /system metrics/i })).toBeVisible()
    await expect(page.getByText("42").first()).toBeVisible()
    await expect(page.getByText("Documents").first()).toBeVisible()
  })

  test("users page lists users and allows edit", async ({ page }) => {
    await page.goto("/admin/users")
    await expect(page.getByRole("heading", { name: "Users", exact: true })).toBeVisible()
    await expect(page.getByRole("cell", { name: "Admin User" })).toBeVisible()
    await expect(page.getByText("jane@company.com")).toBeVisible()
    await page.getByRole("button", { name: /edit/i }).first().click()
    await expect(page.getByRole("button", { name: /save/i })).toBeVisible()
    await expect(page.getByRole("button", { name: /cancel/i })).toBeVisible()
  })

  test("audit page shows logs", async ({ page }) => {
    await page.goto("/admin/audit")
    await expect(page.getByRole("heading", { name: /audit log/i })).toBeVisible()
    await expect(page.getByText("admin@eka.com")).toBeVisible()
    await expect(page.getByText("login")).toBeVisible()
  })

  test("non-admin gets redirected from admin pages", async ({ page }) => {
    await page.route("**/api/v1/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 2, name: "Jane", email: "jane@company.com", department_id: 1, department_name: "Engineering", role_id: 3, role_name: "Employee", created_at: new Date().toISOString() }),
      })
    })
    await page.goto("/admin/metrics")
    await expect(page).toHaveURL(/\/dashboard/)
  })
})

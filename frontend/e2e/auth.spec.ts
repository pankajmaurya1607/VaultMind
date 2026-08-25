import { test, expect } from "@playwright/test"

test.describe("Auth flows", () => {
  test("landing page renders and navigates to login", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByText("Your organization", { exact: false })).toBeVisible()
    await expect(page.getByRole("link", { name: /get started/i }).first()).toBeVisible()
    await page.getByRole("link", { name: /log in/i }).first().click()
    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible()
  })

  test("login form validation", async ({ page }) => {
    await page.goto("/login")
    await page.getByRole("button", { name: /sign in/i }).click()
    await expect(page.getByText(/invalid email/i)).toBeVisible()
  })

  test("login success with mocked API", async ({ page }) => {
    await page.route("**/api/v1/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ access_token: "mock_access", refresh_token: "mock_refresh", token_type: "bearer" }),
      })
    })
    await page.route("**/api/v1/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 1, name: "Admin User", email: "admin@eka.com", department_id: 1, department_name: "Engineering", role_id: 1, role_name: "Admin", created_at: new Date().toISOString() }),
      })
    })
    await page.route("**/api/v1/departments", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Engineering" }]) })
    })
    // also need to mock other authenticated requests that dashboard might trigger implicitly (none)
    await page.goto("/login")
    await page.getByLabel(/email/i).fill("admin@eka.com")
    await page.getByLabel(/password/i).fill("admin123")
    await page.getByRole("button", { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 })
    await expect(page.getByText(/welcome, admin user/i)).toBeVisible()
  })

  test("register page renders and validates", async ({ page }) => {
    await page.route("**/api/v1/departments", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Engineering" }, { id: 2, name: "Marketing" }]) })
    })
    await page.goto("/register")
    await expect(page.getByRole("heading", { name: /create account/i })).toBeVisible()
    await page.getByRole("button", { name: /create account/i }).click()
    // should show name required
    await expect(page.getByText(/name is required/i)).toBeVisible()
  })

  test("unauthenticated redirect to login", async ({ page }) => {
    await page.goto("/dashboard")
    await expect(page).toHaveURL(/\/login/)
  })
})

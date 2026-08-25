import { test, expect } from "@playwright/test"

async function mockAdmin(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, name: "Admin User", email: "admin@eka.com", department_id: 1, department_name: "Engineering", role_id: 1, role_name: "Admin", created_at: new Date().toISOString() }),
    })
  })
  await page.route("**/api/v1/departments", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Engineering" }, { id: 2, name: "Marketing" }]) })
  })
  await page.route("**/api/v1/departments/roles", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([{ id: 1, name: "Admin" }, { id: 2, name: "Manager" }, { id: 3, name: "Employee" }]) })
  })
}

test.describe("Departments", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("access_token", "mock_access")
      localStorage.setItem("refresh_token", "mock_refresh")
    })
    await mockAdmin(page)
  })

  test("departments page shows lists", async ({ page }) => {
    await page.goto("/admin/departments")
    await expect(page.getByRole("heading", { name: /departments.*roles/i })).toBeVisible()
    await expect(page.getByText("Engineering").first()).toBeVisible()
    await expect(page.getByText("Admin").first()).toBeVisible()
    await expect(page.getByText("Marketing").first()).toBeVisible()
  })
})

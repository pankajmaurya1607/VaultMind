import { test, expect } from "@playwright/test"

async function mockAuthenticated(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, name: "Admin User", email: "admin@eka.com", department_id: 1, department_name: "Engineering", role_id: 1, role_name: "Admin", created_at: new Date().toISOString() }),
    })
  })
  // detail first, more specific
  await page.route("**/api/v1/documents/*", async (route) => {
    const url = route.request().url()
    if (url.includes("/documents/") && route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 1, original_filename: "handbook.pdf", file_size: 102400, mime_type: "application/pdf", status: "ready", uploaded_by: 1, department_id: 1, chunk_count: 12, error_message: null, created_at: new Date().toISOString() }),
      })
      return
    }
    if (route.request().method() === "DELETE") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: "Deleted" }) })
      return
    }
    await route.continue()
  })
  await page.route("**/api/v1/documents*", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: 1, original_filename: "handbook.pdf", file_size: 102400, mime_type: "application/pdf", status: "ready", uploaded_by: 1, department_id: 1, chunk_count: 12, error_message: null, created_at: new Date().toISOString() },
            { id: 2, original_filename: "report.csv", file_size: 20480, mime_type: "text/csv", status: "processing", uploaded_by: 1, department_id: 1, chunk_count: 0, error_message: null, created_at: new Date().toISOString() },
          ],
          total: 2,
          skip: 0,
          limit: 100,
        }),
      })
    } else if (route.request().method() === "POST") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: 3, filename: "new.pdf", status: "pending", message: "Uploaded" }) })
    } else {
      await route.continue()
    }
  })
}

test.describe("Documents", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticated(page)
    await page.goto("/documents")
  })

  test("lists documents", async ({ page }) => {
    await expect(page.getByText("Documents").first()).toBeVisible({ timeout: 10000 })
    await expect(page.getByText("handbook.pdf").first()).toBeVisible({ timeout: 10000 })
    await expect(page.getByText("report.csv").first()).toBeVisible()
    await expect(page.getByText("ready").first()).toBeVisible()
  })

  test("filters documents", async ({ page }) => {
    await expect(page.getByText("handbook.pdf").first()).toBeVisible({ timeout: 10000 })
    await page.getByPlaceholder(/filter by filename/i).fill("handbook")
    await expect(page.getByText("handbook.pdf").first()).toBeVisible()
    await expect(page.getByText("report.csv")).not.toBeVisible()
    await page.getByPlaceholder(/filter by filename/i).fill("nonexistent")
    await expect(page.getByText(/no documents match/i)).toBeVisible()
  })

  test("opens detail dialog", async ({ page }) => {
    await expect(page.getByText("handbook.pdf").first()).toBeVisible({ timeout: 10000 })
    await page.getByText("handbook.pdf").first().click()
    await expect(page.getByRole("dialog")).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/detailed info/i)).toBeVisible()
  })

  test("opens upload dialog", async ({ page }) => {
    await page.getByRole("button", { name: /upload/i }).click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByText(/drop a file here/i)).toBeVisible()
    await expect(page.getByText(/max 10 mb/i)).toBeVisible()
  })
})

import { describe, it, expect } from "vitest"
import { cn } from "@/lib/utils"

describe("cn utility", () => {
  it("merges class names", () => {
    expect(cn("p-2", "text-sm")).toBe("p-2 text-sm")
  })
  it("overrides conflicting tailwind classes", () => {
    expect(cn("p-2", "p-4")).toBe("p-4")
  })
  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "visible")).toBe("base visible")
  })
  it("handles empty", () => {
    expect(cn()).toBe("")
  })
})

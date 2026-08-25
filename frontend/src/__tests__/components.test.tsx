import { describe, it, expect } from "vitest"
import { render, screen } from "@/test/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Label } from "@/components/ui/label"

describe("shadcn UI primitives", () => {
  it("renders Button variants", () => {
    render(<Button>Default</Button>)
    expect(screen.getByRole("button", { name: "Default" })).toBeInTheDocument()
  })
  it("renders Button disabled", () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole("button", { name: "Disabled" })).toBeDisabled()
  })
  it("renders Input", () => {
    render(<Input placeholder="test placeholder" />)
    expect(screen.getByPlaceholderText("test placeholder")).toBeInTheDocument()
  })
  it("renders Badge", () => {
    render(<Badge>Ready</Badge>)
    expect(screen.getByText("Ready")).toBeInTheDocument()
  })
  it("renders Card", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
        </CardHeader>
        <CardContent>Content</CardContent>
      </Card>
    )
    expect(screen.getByText("Title")).toBeInTheDocument()
    expect(screen.getByText("Content")).toBeInTheDocument()
  })
  it("renders Skeleton", () => {
    const { container } = render(<Skeleton className="h-4 w-20" />)
    expect(container.firstChild).toHaveClass("animate-pulse")
  })
  it("renders Label", () => {
    render(<Label htmlFor="x">My Label</Label>)
    expect(screen.getByText("My Label")).toBeInTheDocument()
  })
  it("applies custom className via cn", () => {
    render(<Button className="custom-class">Btn</Button>)
    expect(screen.getByRole("button", { name: "Btn" })).toHaveClass("custom-class")
  })
})

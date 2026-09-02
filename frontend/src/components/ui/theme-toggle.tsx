import { Moon, Sun } from "lucide-react"
import { Button } from "./button"
import { useTheme } from "@/context/ThemeContext"

export function ThemeToggle({ collapsed }: { collapsed?: boolean }) {
  const { theme, toggle } = useTheme()
  if (collapsed) {
    return (
      <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme" title={theme === "dark" ? "Light mode" : "Dark mode"}>
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
    )
  }
  return (
    <Button variant="ghost" size="sm" onClick={toggle} className="gap-2 w-full justify-start">
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </Button>
  )
}

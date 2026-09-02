import { useState, useEffect } from "react"
import { Menu } from "lucide-react"
import Sidebar from "./Sidebar"
import CommandBar from "./CommandBar"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"

interface AppLayoutProps {
  children: React.ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [open, setOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("vaultmind_sidebar_collapsed") === "1")

  useEffect(() => {
    localStorage.setItem("vaultmind_sidebar_collapsed", collapsed ? "1" : "0")
  }, [collapsed])

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden md:flex">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="p-0 w-64 border-r">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <Sidebar />
        </SheetContent>
      </Sheet>

      <div className="flex flex-1 flex-col min-w-0">
        <header className="flex h-14 items-center gap-3 border-b bg-card/50 px-4 backdrop-blur-sm">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setOpen(true)} aria-label="Toggle sidebar">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex-1 flex justify-center">
            <div className="w-full max-w-xl">
              <CommandBar />
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-background">{children}</main>
      </div>
    </div>
  )
}

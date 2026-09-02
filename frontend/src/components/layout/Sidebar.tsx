import { NavLink } from "react-router-dom"
import { useAuth, isAdmin } from "@/context/AuthContext"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  LayoutDashboard,
  Files,
  Search,
  MessageSquare,
  Users,
  ScrollText,
  BarChart3,
  Building2,
  LogOut,
  MoreVertical,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react"
import { ThemeToggle } from "@/components/ui/theme-toggle"

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/documents", label: "Documents", icon: Files },
  { to: "/search", label: "Search", icon: Search },
  { to: "/chat", label: "Chat", icon: MessageSquare },
]

const adminItems = [
  { to: "/admin/users", label: "Users", icon: Users },
  { to: "/admin/audit", label: "Audit Log", icon: ScrollText },
  { to: "/admin/metrics", label: "Metrics", icon: BarChart3 },
  { to: "/admin/departments", label: "Departments", icon: Building2 },
]

function NavItem({
  to,
  label,
  icon: Icon,
  collapsed,
  end,
}: {
  to: string
  label: string
  icon: React.ElementType
  collapsed?: boolean
  end?: boolean
}) {
  return (
    <NavLink
      to={to}
      end={end}
      title={collapsed ? label : undefined}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          collapsed && "justify-center px-2",
          isActive
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && label}
    </NavLink>
  )
}

export default function Sidebar({
  collapsed = false,
  onToggle,
}: {
  collapsed?: boolean
  onToggle?: () => void
}) {
  const { user, logout } = useAuth()

  return (
    <aside className={cn("flex h-screen flex-col border-r bg-card transition-all duration-200", collapsed ? "w-16" : "w-64")}>
      <div className={cn("flex h-14 items-center border-b", collapsed ? "justify-center px-2" : "px-5 justify-between")}>
        {!collapsed && (
          <>
            <div className="flex items-center">
              <span className="text-base font-semibold tracking-tight">VaultMind</span>
              <span className="ml-2 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">EKA</span>
            </div>
            {onToggle && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onToggle} aria-label="Collapse sidebar">
                <PanelLeftClose className="h-4 w-4" />
              </Button>
            )}
          </>
        )}
        {collapsed && onToggle && (
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onToggle} aria-label="Expand sidebar">
            <PanelLeftOpen className="h-4 w-4" />
          </Button>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavItem key={item.to} to={item.to} label={item.label} icon={item.icon} collapsed={collapsed} end={item.to === "/dashboard"} />
          ))}
        </div>

        {isAdmin(user) && (
          <>
            <Separator className="my-4" />
            {!collapsed && (
              <p className="px-3 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Admin
              </p>
            )}
            <div className="space-y-1">
              {adminItems.map((item) => (
                <NavItem key={item.to} to={item.to} label={item.label} icon={item.icon} collapsed={collapsed} />
              ))}
            </div>
          </>
        )}
      </nav>

      <div className="border-t p-3 space-y-2">
        <ThemeToggle collapsed={collapsed} />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className={cn("flex h-auto w-full items-center justify-start gap-3 px-2 py-2", collapsed && "justify-center px-1")}>
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary/15 text-primary text-sm font-medium">
                  {user?.name?.charAt(0).toUpperCase() ?? "U"}
                </AvatarFallback>
              </Avatar>
              {!collapsed && (
                <>
                  <div className="flex-1 truncate text-left">
                    <p className="truncate text-sm font-medium leading-none">{user?.name}</p>
                    <p className="truncate text-xs text-muted-foreground">{user?.role_name || "User"}</p>
                  </div>
                  <MoreVertical className="h-4 w-4 text-muted-foreground" />
                </>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user?.name}</p>
                <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
              <LogOut className="h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  )
}

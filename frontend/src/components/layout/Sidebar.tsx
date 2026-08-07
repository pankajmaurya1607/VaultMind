import { NavLink } from "react-router-dom"
import { useAuth } from "../../context/AuthContext"

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: "◈", adminOnly: false },
  { to: "/documents", label: "Documents", icon: "◇", adminOnly: false },
  { to: "/search", label: "Search", icon: "◎", adminOnly: false },
  { to: "/chat", label: "Chat", icon: "◉", adminOnly: false },
]

const adminItems = [
  { to: "/admin/users", label: "Users", icon: "◆", adminOnly: true },
  { to: "/admin/audit", label: "Audit Log", icon: "◈", adminOnly: true },
  { to: "/admin/metrics", label: "Metrics", icon: "◉", adminOnly: true },
]

export default function Sidebar() {
  const { user, logout } = useAuth()

  const roleLabel =
    user?.role_id === 1 ? "Admin" : user?.role_id === 2 ? "Manager" : "Employee"

  return (
    <aside className="w-56 h-screen bg-bg-surface border-r border-border flex flex-col flex-shrink-0">
      <div className="px-5 pt-6 pb-4 border-b border-border">
        <h2 className="text-lg font-semibold text-text tracking-tight">VaultMind</h2>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/dashboard"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-accent/10 text-accent font-medium"
                  : "text-text-muted hover:text-text hover:bg-bg-hover"
              }`
            }
          >
            <span className="text-base w-5 text-center">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}

        {user?.role_id === 1 && (
          <>
            <div className="pt-4 pb-1">
              <p className="px-3 text-xs font-medium text-text-dim uppercase tracking-wider">Admin</p>
            </div>
            {adminItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-accent/10 text-accent font-medium"
                      : "text-text-muted hover:text-text hover:bg-bg-hover"
                  }`
                }
              >
                <span className="text-base w-5 text-center">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="px-4 py-4 border-t border-border">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-accent text-sm font-medium">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text truncate">{user?.name}</p>
            <p className="text-xs text-text-muted">{roleLabel}</p>
          </div>
          <button
            onClick={logout}
            className="text-text-dim hover:text-error transition-colors text-sm p-1"
            title="Sign out"
          >
            ✕
          </button>
        </div>
      </div>
    </aside>
  )
}

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider, useAuth } from "./context/AuthContext"
import { ToastProvider } from "./components/ui/Toast"
import AppLayout from "./components/layout/AppLayout"
import LoginPage from "./pages/LoginPage"
import RegisterPage from "./pages/RegisterPage"
import LandingPage from "./pages/LandingPage"
import DashboardPage from "./pages/DashboardPage"
import DocumentsPage from "./pages/DocumentsPage"
import SearchPage from "./pages/SearchPage"
import ChatPage from "./pages/ChatPage"
import AdminUsersPage from "./pages/AdminUsersPage"
import AdminAuditPage from "./pages/AdminAuditPage"
import AdminMetricsPage from "./pages/AdminMetricsPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center min-h-screen text-text-muted">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return <AppLayout>{children}</AppLayout>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center min-h-screen text-text-muted">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (user.role_id !== 1) return <Navigate to="/dashboard" replace />
  return <AppLayout>{children}</AppLayout>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center min-h-screen text-text-muted">Loading...</div>
  if (user) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/documents" element={<ProtectedRoute><DocumentsPage /></ProtectedRoute>} />
      <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
      <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
      <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
      <Route path="/admin/audit" element={<AdminRoute><AdminAuditPage /></AdminRoute>} />
      <Route path="/admin/metrics" element={<AdminRoute><AdminMetricsPage /></AdminRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

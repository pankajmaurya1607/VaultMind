import { Suspense, lazy } from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider, useAuth, isAdmin } from "./context/AuthContext"
import { Toaster } from "@/components/ui/sonner"
import ErrorBoundary from "./components/ui/ErrorBoundary"
import AppLayout from "./components/layout/AppLayout"

const LoginPage = lazy(() => import("./pages/LoginPage"))
const RegisterPage = lazy(() => import("./pages/RegisterPage"))
const LandingPage = lazy(() => import("./pages/LandingPage"))
const DashboardPage = lazy(() => import("./pages/DashboardPage"))
const DocumentsPage = lazy(() => import("./pages/DocumentsPage"))
const SearchPage = lazy(() => import("./pages/SearchPage"))
const ChatPage = lazy(() => import("./pages/ChatPage"))
const AdminUsersPage = lazy(() => import("./pages/AdminUsersPage"))
const AdminAuditPage = lazy(() => import("./pages/AdminAuditPage"))
const AdminMetricsPage = lazy(() => import("./pages/AdminMetricsPage"))
const AdminDepartmentsPage = lazy(() => import("./pages/AdminDepartmentsPage"))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function LoadingScreen() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="flex flex-col items-center gap-3">
        <span className="h-6 w-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">Loading...</span>
      </div>
    </div>
  )
}

function RouteFallback() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3">
        <span className="h-5 w-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">Loading page...</span>
      </div>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  if (!user) return <Navigate to="/login" replace />
  return <AppLayout>{children}</AppLayout>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  if (!user) return <Navigate to="/login" replace />
  if (!isAdmin(user)) return <Navigate to="/dashboard" replace />
  return <AppLayout>{children}</AppLayout>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingScreen />
  if (user) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="mt-2 text-muted-foreground">Page not found</p>
      <a href="/" className="mt-4 text-sm text-primary hover:underline">Go home</a>
    </div>
  )
}

function AppRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<PublicRoute><LandingPage /></PublicRoute>} />
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/documents" element={<ProtectedRoute><DocumentsPage /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
        <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
        <Route path="/admin/audit" element={<AdminRoute><AdminAuditPage /></AdminRoute>} />
        <Route path="/admin/metrics" element={<AdminRoute><AdminMetricsPage /></AdminRoute>} />
        <Route path="/admin/departments" element={<AdminRoute><AdminDepartmentsPage /></AdminRoute>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <AppRoutes />
            <Toaster richColors position="top-right" closeButton />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

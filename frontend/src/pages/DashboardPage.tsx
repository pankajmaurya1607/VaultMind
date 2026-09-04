import { Link } from "react-router-dom"
import { useAuth } from "@/context/AuthContext"
import { useHealth } from "@/hooks/useHealth"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Files, Search, MessageSquare, ArrowRight, Activity, CheckCircle, AlertCircle } from "lucide-react"

const cards = [
  {
    to: "/documents",
    icon: Files,
    title: "Documents",
    desc: "Upload and manage your knowledge base files. PDF, DOCX, TXT, and MD.",
  },
  {
    to: "/search",
    icon: Search,
    title: "Search",
    desc: "Semantic search across all your indexed documents with highlights.",
  },
  {
    to: "/chat",
    icon: MessageSquare,
    title: "Chat",
    desc: "Ask questions and get AI-powered answers with cited sources.",
  },
]

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: health, isError: healthError } = useHealth()

  return (
    <div className="mx-auto max-w-5xl p-6 animate-fade-in">
      <div className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Welcome, {user?.name}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="font-normal">
                {user?.role_name}
              </Badge>
              <span className="text-sm text-muted-foreground">{user?.department_name}</span>
              <span className="text-muted-foreground">·</span>
              <span className="text-sm text-muted-foreground">{user?.email}</span>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 rounded-lg border bg-card px-3 py-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            {health ? (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-500" /> {health.service} {health.version} · healthy
              </span>
            ) : healthError ? (
              <span className="inline-flex items-center gap-1.5 text-xs text-destructive">
                <AlertCircle className="h-3.5 w-3.5" /> offline
              </span>
            ) : (
              <span className="text-xs text-muted-foreground">checking…</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <Link key={c.to} to={c.to} className="group">
            <Card className="h-full transition-colors hover:border-primary/30 hover:shadow-md">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <c.icon className="h-5 w-5" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-0 -translate-x-2 transition-all" />
                </div>
                <CardTitle className="text-base">{c.title}</CardTitle>
                <CardDescription className="text-sm leading-relaxed">{c.desc}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="text-xs font-medium text-primary group-hover:underline">Open {c.title} →</span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Card className="mt-6 border-dashed">
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">
            VaultMind is your organization&apos;s knowledge, unlocked by AI. Upload documents, search semantically, and chat with your data — all with role-based access control.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

import { useAuth } from "../context/AuthContext"

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold text-text mb-1">
        Welcome, {user?.name}
      </h1>
      <p className="text-sm text-text-muted mb-8">
        {user?.role_name} &middot; {user?.department_name}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <a
          href="/documents"
          className="bg-bg-surface border border-border rounded-xl p-5 hover:border-accent/30 transition-colors group"
        >
          <p className="text-2xl mb-2 text-text-muted group-hover:text-accent transition-colors">◇</p>
          <h3 className="text-sm font-medium text-text mb-1">Documents</h3>
          <p className="text-xs text-text-muted">Upload and manage your knowledge base files</p>
        </a>
        <a
          href="/search"
          className="bg-bg-surface border border-border rounded-xl p-5 hover:border-accent/30 transition-colors group"
        >
          <p className="text-2xl mb-2 text-text-muted group-hover:text-accent transition-colors">◎</p>
          <h3 className="text-sm font-medium text-text mb-1">Search</h3>
          <p className="text-xs text-text-muted">Search across all your indexed documents</p>
        </a>
        <a
          href="/chat"
          className="bg-bg-surface border border-border rounded-xl p-5 hover:border-accent/30 transition-colors group"
        >
          <p className="text-2xl mb-2 text-text-muted group-hover:text-accent transition-colors">◉</p>
          <h3 className="text-sm font-medium text-text mb-1">Chat</h3>
          <p className="text-xs text-text-muted">Ask questions and get AI-powered answers</p>
        </a>
      </div>
    </div>
  )
}

import { Link } from "react-router-dom"

const features = [
  {
    icon: "◇",
    title: "Document Management",
    desc: "Upload PDF, DOCX, CSV, and more. Automatic parsing, chunking, and indexing.",
  },
  {
    icon: "◎",
    title: "AI-Powered Search",
    desc: "Semantic search across all your documents with relevance scoring and highlights.",
  },
  {
    icon: "◉",
    title: "Smart Chat",
    desc: "Ask questions in natural language. Get answers with cited sources and confidence scores.",
  },
  {
    icon: "◈",
    title: "Role-Based Access",
    desc: "Admin, Manager, and Employee roles with department-scoped permissions.",
  },
  {
    icon: "◆",
    title: "Real-Time Processing",
    desc: "Documents are processed asynchronously with status tracking from upload to ready.",
  },
  {
    icon: "◈",
    title: "Audit Trail",
    desc: "Every action is logged. Full visibility into who did what and when.",
  },
]

const steps = [
  { num: "01", title: "Upload Documents", desc: "Drop files into your knowledge base. All common formats supported." },
  { num: "02", title: "AI Indexes Content", desc: "Documents are parsed, chunked, and embedded into a vector database." },
  { num: "03", title: "Ask Anything", desc: "Search or chat in natural language. Get accurate answers with sources." },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-base text-text">
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            VaultMind
          </Link>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm text-text-muted hover:text-text transition-colors px-3 py-2"
            >
              Log in
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium text-white bg-accent hover:bg-accent-hover transition-colors px-4 py-2 rounded-lg"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-accent/[0.03] to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto px-6 pt-24 pb-28 text-center relative">
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-tight">
            Your organization's knowledge,{" "}
            <span className="text-accent">unlocked by AI</span>
          </h1>
          <p className="mt-4 text-lg text-text-muted max-w-2xl mx-auto leading-relaxed">
            Upload documents, search semantically, and chat with your data — all with
            role-based access control and full audit trails.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link
              to="/register"
              className="px-6 py-3 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-xl transition-colors"
            >
              Get started free
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 text-sm font-medium text-text-muted hover:text-text border border-border hover:border-accent/30 rounded-xl transition-colors"
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-28">
        <h2 className="text-2xl font-semibold text-center mb-12">Everything your team needs</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-bg-surface border border-border rounded-xl p-5 hover:border-accent/20 transition-colors"
            >
              <span className="text-2xl text-accent mb-3 block">{f.icon}</span>
              <h3 className="text-sm font-medium text-text mb-1.5">{f.title}</h3>
              <p className="text-sm text-text-muted leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-border">
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <h2 className="text-2xl font-semibold mb-12">How it works</h2>
          <div className="grid sm:grid-cols-3 gap-8 text-left">
            {steps.map((s) => (
              <div key={s.num}>
                <span className="text-4xl font-semibold text-accent/30">{s.num}</span>
                <h3 className="text-base font-medium text-text mt-2 mb-1.5">{s.title}</h3>
                <p className="text-sm text-text-muted leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-8 flex items-center justify-between text-sm text-text-dim">
          <span>VaultMind</span>
          <span>&copy; {new Date().getFullYear()}</span>
        </div>
      </footer>
    </div>
  )
}

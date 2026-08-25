import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText, Search, MessageSquare, Shield, Clock, ScrollText, ArrowRight, Sparkles } from "lucide-react"

const features = [
  { icon: FileText, title: "Document Management", desc: "Upload PDF, DOCX, CSV, and more. Automatic parsing, chunking, and indexing." },
  { icon: Search, title: "AI-Powered Search", desc: "Semantic search across all your documents with relevance scoring and highlights." },
  { icon: MessageSquare, title: "Smart Chat", desc: "Ask questions in natural language. Get answers with cited sources and confidence scores." },
  { icon: Shield, title: "Role-Based Access", desc: "Admin, Manager, and Employee roles with department-scoped permissions." },
  { icon: Clock, title: "Real-Time Processing", desc: "Documents are processed asynchronously with status tracking from upload to ready." },
  { icon: ScrollText, title: "Audit Trail", desc: "Every action is logged. Full visibility into who did what and when." },
]

const steps = [
  { num: "01", title: "Upload Documents", desc: "Drop files into your knowledge base. All common formats supported." },
  { num: "02", title: "AI Indexes Content", desc: "Documents are parsed, chunked, and embedded into a vector database." },
  { num: "03", title: "Ask Anything", desc: "Search or chat in natural language. Get accurate answers with sources." },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Sparkles className="h-4 w-4" />
            </div>
            VaultMind
          </Link>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link to="/login">Log in</Link>
            </Button>
            <Button asChild>
              <Link to="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/[0.04] to-transparent pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative mx-auto max-w-4xl px-6 pt-20 pb-24 text-center">
          <Badge variant="secondary" className="mb-4 gap-1">
            <Sparkles className="h-3 w-3" /> Enterprise Knowledge Assistant
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-tight">
            Your organization&apos;s knowledge, <span className="text-primary">unlocked by AI</span>
          </h1>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Upload documents, search semantically, and chat with your data — all with role-based access control and full audit trails.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Button size="lg" asChild className="gap-2">
              <Link to="/register">
                Get started free <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/login">Sign in</Link>
            </Button>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">No credit card required · 10MB per file · All formats supported</p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <h2 className="text-2xl font-semibold text-center mb-2">Everything your team needs</h2>
        <p className="text-sm text-muted-foreground text-center mb-8">Built for security, speed, and scale</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => (
            <Card key={f.title} className="hover:border-primary/20 transition-colors">
              <CardHeader>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <f.icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-sm">{f.title}</CardTitle>
                <CardDescription className="text-sm leading-relaxed">{f.desc}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-t bg-muted/30">
        <div className="mx-auto max-w-4xl px-6 py-16 text-center">
          <h2 className="text-2xl font-semibold mb-10">How it works</h2>
          <div className="grid sm:grid-cols-3 gap-8 text-left">
            {steps.map((s) => (
              <div key={s.num} className="relative">
                <span className="text-4xl font-semibold text-primary/15">{s.num}</span>
                <h3 className="text-base font-medium mt-2 mb-1.5">{s.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-12">
        <Card className="bg-primary text-primary-foreground border-primary">
          <CardContent className="flex flex-col sm:flex-row items-center justify-between gap-4 py-6">
            <div>
              <h3 className="font-semibold">Ready to unlock your knowledge?</h3>
              <p className="text-sm text-primary-foreground/80">Start for free and see VaultMind in action.</p>
            </div>
            <Button variant="secondary" size="lg" asChild>
              <Link to="/register">Get started</Link>
            </Button>
          </CardContent>
        </Card>
      </section>

      <footer className="border-t">
        <div className="mx-auto max-w-6xl px-6 py-6 flex items-center justify-between text-sm text-muted-foreground">
          <span className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" /> VaultMind
          </span>
          <span>© {new Date().getFullYear()} VaultMind · Enterprise Knowledge Assistant</span>
        </div>
      </footer>
    </div>
  )
}

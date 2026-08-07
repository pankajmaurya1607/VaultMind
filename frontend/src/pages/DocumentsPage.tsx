import { useState, useMemo } from "react"
import { useDocuments, useDeleteDocument } from "../hooks/useDocuments"
import { useAuth } from "../context/AuthContext"
import UploadModal from "../components/ui/UploadModal"

const statusColor: Record<string, string> = {
  ready: "bg-accent/10 text-accent border-accent/20",
  pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  processing: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  failed: "bg-error/10 text-error border-error/20",
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  })
}

export default function DocumentsPage() {
  const { data: documents, isLoading, error } = useDocuments()
  const deleteDoc = useDeleteDocument()
  const { user } = useAuth()
  const isAdmin = user?.role_id === 1
  const [uploadOpen, setUploadOpen] = useState(false)
  const [search, setSearch] = useState("")

  const filtered = useMemo(() => {
    if (!documents) return []
    if (!search.trim()) return documents
    const q = search.toLowerCase()
    return documents.filter((d) => d.original_filename.toLowerCase().includes(q))
  }, [documents, search])

  const handleDelete = (id: number, name: string) => {
    if (window.confirm(`Delete "${name}"?`)) {
      deleteDoc.mutate(id)
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-text">Documents</h1>
          <p className="text-sm text-text-muted mt-0.5">
            {documents ? `${documents.length} document${documents.length !== 1 ? "s" : ""}` : "Loading..."}
          </p>
        </div>
        <button
          onClick={() => setUploadOpen(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-accent hover:bg-accent-hover rounded-lg transition-colors flex items-center gap-2"
        >
          + Upload
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by filename..."
          className="w-full max-w-xs bg-bg-surface border border-border rounded-lg px-3.5 py-2 text-sm text-text placeholder:text-text-dim focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
        />
      </div>

      {isLoading && (
        <div className="text-sm text-text-muted py-12 text-center">Loading documents...</div>
      )}

      {error && (
        <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-3">
          Failed to load documents
        </div>
      )}

      {!isLoading && !error && filtered.length === 0 && (
        <div className="text-sm text-text-muted py-12 text-center">
          {search ? "No documents match your filter." : "No documents yet. Upload your first document."}
        </div>
      )}

      {filtered.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted text-xs uppercase tracking-wider">
                <th className="text-left py-3 pr-4 font-medium">Name</th>
                <th className="text-left py-3 pr-4 font-medium">Type</th>
                <th className="text-left py-3 pr-4 font-medium">Size</th>
                <th className="text-left py-3 pr-4 font-medium">Status</th>
                <th className="text-left py-3 pr-4 font-medium">Chunks</th>
                <th className="text-left py-3 pr-4 font-medium">Uploaded</th>
                {isAdmin && <th className="text-right py-3 font-medium">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filtered.map((doc) => (
                <tr key={doc.id} className="border-b border-border/50 hover:bg-bg-hover transition-colors">
                  <td className="py-3 pr-4 text-text font-medium truncate max-w-[260px]" title={doc.original_filename}>
                    {doc.original_filename}
                  </td>
                  <td className="py-3 pr-4 text-text-muted">{doc.mime_type}</td>
                  <td className="py-3 pr-4 text-text-muted whitespace-nowrap">{formatSize(doc.file_size)}</td>
                  <td className="py-3 pr-4">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusColor[doc.status] || ""}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-text-muted">{doc.chunk_count}</td>
                  <td className="py-3 pr-4 text-text-muted whitespace-nowrap">{formatDate(doc.created_at)}</td>
                  {isAdmin && (
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        disabled={deleteDoc.isPending}
                        className="text-text-dim hover:text-error transition-colors text-xs px-2 py-1"
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api'
import { ResearchShimmer } from '../components/Shimmer'

export default function Research() {
  const [dash, setDash] = useState<any>(null)
  const [notes, setNotes] = useState<any[]>([])
  const [papers, setPapers] = useState<any[]>([])
  const [methodology, setMethodology] = useState<any>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('Research Findings')
  const [paperTitle, setPaperTitle] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  async function refresh() {
    setDash(await api.researchDashboard())
    setNotes((await api.notes()).notes || [])
    setPapers((await api.papers()).papers || [])
    setMethodology(await api.methodology())
  }

  useEffect(() => {
    setLoading(true)
    refresh()
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <ResearchShimmer />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Research Center</h2>
        <p className="text-[var(--muted)] mt-1">Notes, literature, methodology draft, and report export — all local.</p>
      </header>

      {dash && (
        <div className="card p-5 space-y-2">
          <h3 className="font-semibold">{dash.research_title}</h3>
          <p className="text-sm text-[var(--muted)]">Experiments: {dash.completed_experiments} · Papers: {dash.papers}</p>
          <ul className="text-sm list-disc pl-5">
            {(dash.research_questions || []).map((q: string) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5 space-y-3">
          <h3 className="font-semibold">Research notes</h3>
          <input
            className="w-full rounded-xl border border-[var(--line)] px-3 py-2"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <select
            className="w-full rounded-xl border border-[var(--line)] px-3 py-2"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {(dash?.note_categories || []).map((c: string) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <textarea
            className="w-full rounded-xl border border-[var(--line)] px-3 py-2"
            rows={4}
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <button
            className="rounded-xl bg-[var(--royal)] text-white px-4 py-2"
            onClick={async () => {
              await api.createNote({ title, category, content, tags: [] })
              setTitle('')
              setContent('')
              await refresh()
            }}
          >
            Save note
          </button>
          <div className="space-y-2 max-h-80 overflow-auto">
            {notes.map((n) => (
              <div key={n.id} className="rounded-xl bg-[var(--card)] p-3 text-sm">
                <div className="font-medium">{n.title}</div>
                <div className="text-xs text-[var(--muted)]">{n.category}</div>
                <p className="mt-1">{n.content}</p>
                <button
                  className="mt-2 text-xs text-red-600"
                  onClick={async () => {
                    await api.deleteNote(n.id)
                    await refresh()
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5 space-y-3">
          <h3 className="font-semibold">Literature review</h3>
          <p className="text-xs text-[var(--muted)]">
            Add only manually verified free references. Do not invent citations.
          </p>
          <input
            className="w-full rounded-xl border border-[var(--line)] px-3 py-2"
            placeholder="Paper title"
            value={paperTitle}
            onChange={(e) => setPaperTitle(e.target.value)}
          />
          <button
            className="rounded-xl border border-[var(--line)] px-4 py-2"
            onClick={async () => {
              if (!paperTitle.trim()) return
              await api.createPaper({ title: paperTitle, relevance: 'manual entry' })
              setPaperTitle('')
              await refresh()
            }}
          >
            Add paper stub
          </button>
          <div className="space-y-2 max-h-80 overflow-auto">
            {papers.map((p) => (
              <div key={p.id} className="rounded-xl bg-[var(--card)] p-3 text-sm">
                <div className="font-medium">{p.title}</div>
                <div className="text-xs text-[var(--muted)]">{p.authors || 'authors TBD'} · {p.year || 'year TBD'}</div>
              </div>
            ))}
            {!papers.length && <p className="text-sm text-[var(--muted)]">No papers yet.</p>}
          </div>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold mb-2">Methodology (DRAFT)</h3>
        <pre className="text-xs overflow-auto max-h-64 bg-[var(--card)] p-3 rounded-xl">
          {JSON.stringify(methodology, null, 2)}
        </pre>
      </div>

      <div className="card p-5 flex flex-wrap gap-3">
        <button
          className="rounded-xl bg-[var(--royal)] text-white px-4 py-2"
          onClick={async () => {
            const res = await api.exportReport('complete', 'all')
            setMessage(`Exported: ${JSON.stringify(res.paths)}`)
          }}
        >
          Export complete report (MD/DOCX/PDF)
        </button>
        {message && <p className="text-sm text-[var(--muted)] break-all">{message}</p>}
      </div>
    </div>
  )
}

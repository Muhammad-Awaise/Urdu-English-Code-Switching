import { useEffect, useState } from 'react'
import { api } from '../api'
import { AnnotationShimmer } from '../components/Shimmer'
import { labelClass } from '../lib/labelStyles'

const LABELS = ['URDU_ROMAN', 'ENGLISH', 'AMBIGUOUS', 'UNKNOWN', 'OTHER']

export default function Annotation() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [datasetId, setDatasetId] = useState<number | null>(null)
  const [records, setRecords] = useState<any[]>([])
  const [index, setIndex] = useState(0)
  const [unlabeledOnly, setUnlabeledOnly] = useState(false)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const ds = await api.datasets()
      setDatasets(ds.datasets || [])
      const id = datasetId || ds.datasets?.[0]?.id
      if (!id) {
        setRecords([])
        return
      }
      setDatasetId(id)
      const rec = await api.datasetRecords(id, unlabeledOnly)
      setRecords(rec.records || [])
      setIndex(0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load().catch((e) => setMessage(e.message))
  }, [unlabeledOnly])

  const current = records[index]

  if (loading) return <AnnotationShimmer />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Annotation Workspace</h2>
        <p className="text-[var(--muted)] mt-1">
          Assign word-level labels. Guideline: prefer AMBIGUOUS over forcing a language when unsure.
        </p>
      </header>

      <div className="card p-4 flex flex-wrap gap-3 items-center">
        <select
          className="rounded-xl border border-[var(--line)] px-3 py-2"
          value={datasetId ?? ''}
          onChange={async (e) => {
            const id = Number(e.target.value)
            setDatasetId(id)
            const rec = await api.datasetRecords(id, unlabeledOnly)
            setRecords(rec.records || [])
            setIndex(0)
          }}
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <label className="text-sm flex items-center gap-2">
          <input type="checkbox" checked={unlabeledOnly} onChange={(e) => setUnlabeledOnly(e.target.checked)} />
          Unannotated / unknown filter
        </label>
        <div className="text-sm text-[var(--muted)]">
          {records.length ? `${index + 1} / ${records.length}` : 'No records'}
        </div>
      </div>

      {message && <p className="text-sm text-red-600">{message}</p>}

      {current ? (
        <div className="card p-6 space-y-4">
          <div className="text-xs text-[var(--muted)]">
            {current.sentence_id} · split={current.split || 'unassigned'}
          </div>
          <p className="text-xl leading-relaxed">{current.text}</p>
          <div className="space-y-3">
            {current.annotations.map((a: any) => (
              <div key={a.id} className="flex flex-wrap items-center gap-3 rounded-xl bg-[var(--card)] px-3 py-2">
                <span className={`token-chip ${labelClass(a.label)}`}>{a.token}</span>
                <select
                  className="rounded-lg border border-[var(--line)] px-2 py-1 text-sm"
                  value={a.label}
                  onChange={async (e) => {
                    await api.updateAnnotation(a.id, { label: e.target.value })
                    setMessage(`Updated ${a.token} → ${e.target.value}`)
                    const rec = await api.datasetRecords(datasetId!, unlabeledOnly)
                    setRecords(rec.records || [])
                  }}
                >
                  {LABELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
                <label className="text-xs flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={!!a.uncertain}
                    onChange={async (e) => {
                      await api.updateAnnotation(a.id, { uncertain: e.target.checked })
                      const rec = await api.datasetRecords(datasetId!, unlabeledOnly)
                      setRecords(rec.records || [])
                    }}
                  />
                  uncertain
                </label>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-xl border border-[var(--line)] px-4 py-2"
              disabled={index === 0}
              onClick={() => setIndex((i) => Math.max(0, i - 1))}
            >
              Previous
            </button>
            <button
              className="rounded-xl bg-[var(--royal)] text-white px-4 py-2"
              disabled={index >= records.length - 1}
              onClick={() => setIndex((i) => Math.min(records.length - 1, i + 1))}
            >
              Next
            </button>
          </div>
        </div>
      ) : (
        <p className="text-[var(--muted)]">No annotation records available.</p>
      )}

      <div className="card p-5 text-sm text-[var(--muted)] space-y-2">
        <h3 className="font-semibold text-[var(--ink)]">Annotation guideline (short)</h3>
        <p>URDU_ROMAN: Romanized Urdu lexical items (main, hai, kar, raha).</p>
        <p>ENGLISH: English lexical items (university, admission, apply).</p>
        <p>AMBIGUOUS: Valid in both or unclear without context (to, so, me).</p>
        <p>UNKNOWN: Not confidently identifiable. OTHER: punctuation/numbers/URLs/emojis.</p>
      </div>
    </div>
  )
}

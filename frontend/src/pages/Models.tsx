import { useEffect, useState } from 'react'
import { api } from '../api'
import { ListCardsShimmer } from '../components/Shimmer'

export default function Models() {
  const [data, setData] = useState<any>(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  async function refresh() {
    setLoading(true)
    try {
      setData(await api.models())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh().catch((e) => setMessage(e.message))
  }, [])

  if (loading && !data) return <ListCardsShimmer label="Loading models" rows={3} titleWidth="w-64" />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Model Registry</h2>
        <p className="text-[var(--muted)] mt-1">
          Activate a trained artifact for analyzer inference. Active model is never overwritten automatically.
        </p>
      </header>

      <div className="card p-4 text-sm">
        Fallback when inactive: <strong>{data?.fallback?.name}</strong> ({data?.fallback?.version})
      </div>

      {message && <p className="text-sm text-[var(--royal)]">{message}</p>}

      <div className="space-y-3">
        {(data?.models || []).map((m: any) => (
          <div key={m.id} className="card p-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="font-semibold">
                {m.name} <span className="text-sm text-[var(--muted)]">{m.version}</span>
                {m.is_active && (
                  <span className="ml-2 text-xs rounded-full bg-green-100 text-green-700 px-2 py-0.5">ACTIVE</span>
                )}
              </div>
              <div className="text-xs text-[var(--muted)]">
                {m.architecture} · {m.artifact_path}
              </div>
              <div className="text-xs mt-1">
                Test macro F1: {m.metrics?.test?.macro_f1 ?? '—'}
              </div>
            </div>
            <div className="flex gap-2">
              {!m.is_active ? (
                <button
                  className="rounded-xl bg-[var(--royal)] text-white px-3 py-2 text-sm"
                  onClick={async () => {
                    await api.activateModel(m.id)
                    setMessage(`Activated ${m.name}`)
                    await refresh()
                  }}
                >
                  Activate
                </button>
              ) : (
                <button
                  className="rounded-xl border border-[var(--line)] px-3 py-2 text-sm"
                  onClick={async () => {
                    await api.deactivateModel(m.id)
                    setMessage('Deactivated — dictionary baseline in use')
                    await refresh()
                  }}
                >
                  Deactivate
                </button>
              )}
            </div>
          </div>
        ))}
        {!data?.models?.length && (
          <p className="text-[var(--muted)]">No registered trained models yet.</p>
        )}
      </div>
    </div>
  )
}

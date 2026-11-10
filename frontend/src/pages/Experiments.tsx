import { useEffect, useState } from 'react'
import { api } from '../api'
import { ListCardsShimmer } from '../components/Shimmer'

export default function Experiments() {
  const [experiments, setExperiments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .experiments()
      .then((d) => setExperiments(d.experiments || []))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <ListCardsShimmer label="Loading experiments" rows={3} />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Experiment Tracking</h2>
        <p className="text-[var(--muted)] mt-1">
          Experiment records are created automatically when training completes.
        </p>
      </header>
      <div className="space-y-3">
        {experiments.map((e) => (
          <div key={e.experiment_id} className="card p-4">
            <div className="font-semibold">{e.experiment_id}</div>
            <div className="text-sm text-[var(--muted)]">
              {e.model_type} · {e.created_at}
            </div>
            <pre className="mt-3 text-xs overflow-auto bg-[var(--card)] p-3 rounded-xl max-h-48">
              {JSON.stringify(e.results, null, 2)}
            </pre>
          </div>
        ))}
        {!experiments.length && <p className="text-[var(--muted)]">No experiments yet.</p>}
      </div>
    </div>
  )
}

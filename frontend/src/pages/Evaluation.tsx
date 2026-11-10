import { useEffect, useState } from 'react'
import { api } from '../api'
import { EvaluationShimmer } from '../components/Shimmer'
import { formatMetric } from '../lib/format'

export default function Evaluation() {
  const [compare, setCompare] = useState<any>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [evalData, setEvalData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .compare()
      .then(setCompare)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selected) api.modelEval(selected).then(setEvalData)
  }, [selected])

  if (loading) return <EvaluationShimmer />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Model Evaluation</h2>
        <p className="text-[var(--muted)] mt-1">
          Metrics come from real held-out predictions stored after local training — never fabricated.
        </p>
      </header>

      <div className="card p-5 overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="text-left text-[var(--muted)]">
              <th className="py-2 pr-4 font-semibold whitespace-nowrap">Model</th>
              <th className="py-2 px-4 font-semibold whitespace-nowrap">Architecture</th>
              <th className="py-2 px-4 font-semibold whitespace-nowrap text-right">Accuracy</th>
              <th className="py-2 px-4 font-semibold whitespace-nowrap text-right">Macro F1</th>
              <th className="py-2 px-4 font-semibold whitespace-nowrap text-right">Weighted F1</th>
              <th className="py-2 pl-4 font-semibold whitespace-nowrap text-right">Train time</th>
            </tr>
          </thead>
          <tbody>
            {(compare?.models || []).map((m: any) => (
              <tr
                key={m.model_id}
                className="border-t border-[var(--line)] cursor-pointer hover:bg-[var(--card)]"
                onClick={() => setSelected(m.model_id)}
              >
                <td className="py-2.5 pr-4 max-w-[220px]">
                  <div className="font-medium truncate" title={`${m.name} ${m.version}`}>
                    {m.name}
                  </div>
                  <div className="text-xs text-[var(--muted)] truncate">{m.version}</div>
                </td>
                <td className="py-2.5 px-4 whitespace-nowrap">{m.architecture}</td>
                <td className="py-2.5 px-4 tabular-nums text-right whitespace-nowrap">
                  {formatMetric(m.accuracy)}
                </td>
                <td className="py-2.5 px-4 tabular-nums text-right whitespace-nowrap">
                  {formatMetric(m.macro_f1)}
                </td>
                <td className="py-2.5 px-4 tabular-nums text-right whitespace-nowrap">
                  {formatMetric(m.weighted_f1)}
                </td>
                <td className="py-2.5 pl-4 tabular-nums text-right whitespace-nowrap">
                  {m.train_time_sec == null ? '—' : `${formatMetric(m.train_time_sec, 3)}s`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!compare?.models?.length && (
          <p className="text-sm text-[var(--muted)] mt-3">No evaluated models yet. Train a model first.</p>
        )}
      </div>

      {evalData && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card p-5">
            <h3 className="font-semibold mb-3">Confusion matrix</h3>
            <pre className="text-xs overflow-auto bg-[var(--card)] p-3 rounded-xl">
              {JSON.stringify(evalData.evaluations?.[0]?.confusion_matrix || evalData.model.metrics?.test?.confusion_matrix, null, 2)}
            </pre>
          </div>
          <div className="card p-5">
            <h3 className="font-semibold mb-3">Misclassified examples</h3>
            <pre className="text-xs overflow-auto max-h-80 bg-[var(--card)] p-3 rounded-xl">
              {JSON.stringify(evalData.evaluations?.[0]?.misclassified?.slice(0, 30) || [], null, 2)}
            </pre>
            <ul className="mt-3 text-sm text-[var(--muted)] list-disc pl-5">
              {(evalData.error_analysis_hints || []).map((h: string) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

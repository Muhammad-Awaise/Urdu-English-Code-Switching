import { useState } from 'react'
import { api } from '../api'
import { ShimmerBlock } from '../components/Shimmer'

export default function Preprocessing() {
  const [text, setText] = useState('Main achha university mein admission apply kar rha hoon!!!')
  const [romanNorm, setRomanNorm] = useState(true)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function run() {
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const data = await api.preprocess({
        text,
        roman_urdu_normalize: romanNorm,
        lowercase: true,
        collapse_repeated_chars: true,
      })
      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Preprocessing Laboratory</h2>
        <p className="text-[var(--muted)] mt-1">
          Compare original, cleaned, normalized, and tokenized text. Normalization is configurable.
        </p>
      </header>

      <div className="card p-5 space-y-4">
        <textarea
          className="w-full rounded-2xl border border-[var(--line)] p-4 bg-[var(--card)]"
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <label className="text-sm flex items-center gap-2">
          <input type="checkbox" checked={romanNorm} onChange={(e) => setRomanNorm(e.target.checked)} />
          Roman Urdu spelling normalization
        </label>
        <button onClick={run} className="rounded-xl bg-[var(--royal)] text-white px-4 py-2">
          Run preprocessing
        </button>
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </div>

      {loading && (
        <div className="grid gap-4 lg:grid-cols-2" aria-busy="true">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="card p-5 space-y-3">
              <ShimmerBlock className="h-5 w-48" />
              <ShimmerBlock className="h-4 w-full" />
              <ShimmerBlock className="h-4 w-5/6" />
              <ShimmerBlock className="h-4 w-full" />
              <ShimmerBlock className="h-4 w-4/5" />
            </div>
          ))}
        </div>
      )}

      {result && !loading && (
        <div className="grid gap-4 lg:grid-cols-2">
          {(['with_preprocessing', 'without_roman_normalization'] as const).map((key) => (
            <div key={key} className="card p-5 space-y-2 text-sm">
              <h3 className="font-semibold">{key.replaceAll('_', ' ')}</h3>
              <p><span className="text-[var(--muted)]">Original:</span> {result[key].original}</p>
              <p><span className="text-[var(--muted)]">Cleaned:</span> {result[key].cleaned}</p>
              <p><span className="text-[var(--muted)]">Normalized:</span> {result[key].normalized}</p>
              <p><span className="text-[var(--muted)]">Tokenized:</span> {result[key].tokenized.join(' | ')}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

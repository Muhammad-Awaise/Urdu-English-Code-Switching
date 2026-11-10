import { useEffect, useState } from 'react'
import { api } from '../api'
import { SettingsShimmer } from '../components/Shimmer'

export default function Settings() {
  const [settings, setSettings] = useState<any>(null)

  useEffect(() => {
    api.settings().then(setSettings)
  }, [])

  if (!settings) return <SettingsShimmer />

  return (
    <div className="space-y-6">
      <header>
        <h2 className="brand-serif text-3xl">Settings</h2>
        <p className="text-[var(--muted)] mt-1">Local configuration. No API keys or paid services.</p>
      </header>
      <div className="card p-5 space-y-2 text-sm">
        <p><strong>App:</strong> {settings.app_name}</p>
        <p><strong>Database:</strong> {settings.database_url}</p>
        <p><strong>CS min tokens / language:</strong> {settings.cs_min_tokens_per_language}</p>
        <p><strong>CS min confidence:</strong> {settings.cs_min_confidence}</p>
        <p><strong>Default split:</strong> {JSON.stringify(settings.default_split)}</p>
        <p><strong>Random seed:</strong> {settings.random_seed}</p>
        <p><strong>Zero paid resources:</strong> {String(settings.zero_paid_resources)}</p>
      </div>
    </div>
  )
}

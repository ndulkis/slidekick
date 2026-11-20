import { useEffect, useState } from 'react'
import { api } from '../core/api'

type Profile = { name: string; bindings: Record<string, string> }
type ProfilesResponse = { profiles: Profile[]; active: string | null; state: string }

function GestureProfileSection() {
  const [data, setData] = useState<ProfilesResponse | null>(null)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    api<ProfilesResponse>('/profiles').then(
      (res) => {
        if (!cancelled && res.ok) {
          setData(res.body)
          setSelected(res.body.active ?? res.body.profiles[0]?.name ?? '')
        }
      },
      () => { if (!cancelled) setError('Unable to load gesture profiles.') },
    )
    return () => { cancelled = true }
  }, [])

  async function activate() {
    if (!selected || busy) return
    setBusy(true)
    setError('')
    try {
      const res = await api<{ active?: string; state?: string; error?: string }>(
        '/profiles/active', 'PUT', { name: selected },
      )
      if (!res.ok) {
        setError(res.body.error ?? 'Profile activation failed.')
      } else {
        setData((old) => old ? { ...old, active: res.body.active ?? null,
          state: res.body.state ?? old.state } : old)
      }
    } catch {
      setError('Unable to contact SlideKick.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section aria-labelledby="gesture-profile-title">
      <h2 id="gesture-profile-title">Gesture profiles</h2>
      <p>Active profile: <strong>{data?.active ?? 'Default controller bindings'}</strong></p>
      <p>Pause the presentation session before activating another profile.</p>
      <label htmlFor="gesture-profile-select">Select gesture profile</label>{' '}
      <select id="gesture-profile-select" value={selected}
        onChange={(e) => setSelected(e.target.value)}
        disabled={busy || !data?.profiles.length}>
        {data?.profiles.map((profile) => (
          <option key={profile.name} value={profile.name}>{profile.name}</option>
        ))}
      </select>{' '}
      <button type="button" onClick={() => void activate()}
        disabled={busy || !selected || selected === data?.active}>
        {busy ? 'Activating...' : 'Activate profile'}
      </button>
      {error && <p role="alert">{error}</p>}
      {data?.profiles.find((p) => p.name === selected) && (
        <p>Bindings: {Object.entries(data.profiles.find((p) => p.name === selected)!.bindings)
          .map(([gesture, command]) => `${gesture} → ${command}`).join(', ')}</p>
      )}
    </section>
  )
}

export default GestureProfileSection

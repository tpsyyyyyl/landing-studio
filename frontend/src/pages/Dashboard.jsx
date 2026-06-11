import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, downloadZip } from '../api'
import Shell from '../components/Shell'

const styleBadge = {
  dark: 'bg-indigo-500/15 text-indigo-300',
  light: 'bg-slate-200/15 text-slate-200',
  vibrant: 'bg-pink-500/15 text-pink-300',
}

export default function Dashboard() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/generations').then(setItems).catch((e) => setError(e.message))
  }, [])

  async function remove(id) {
    if (!window.confirm('Delete this landing page?')) return
    await api(`/api/generations/${id}`, { method: 'DELETE' })
    setItems(items.filter((g) => g.id !== id))
  }

  return (
    <Shell>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Your landing pages</h1>
          <p className="mt-1 text-sm text-slate-400">
            {items ? `${items.length} generated` : 'Loading…'}
          </p>
        </div>
        <Link
          to="/new"
          className="rounded-xl bg-accent px-5 py-2.5 font-semibold text-white shadow-lg shadow-accent/30 transition hover:bg-accent-soft"
        >
          + New page
        </Link>
      </div>

      {error && <p className="mt-6 text-red-400">{error}</p>}

      {items && items.length === 0 && (
        <div className="mt-16 rounded-2xl border border-dashed border-line p-16 text-center">
          <p className="text-lg font-semibold text-white">No pages yet</p>
          <p className="mt-2 text-sm text-slate-400">
            Generate your first landing page — it takes about a minute.
          </p>
        </div>
      )}

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {items?.map((g) => (
          <div
            key={g.id}
            className="group flex flex-col rounded-2xl border border-line bg-panel p-5 transition hover:-translate-y-1 hover:border-slate-600"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-bold text-white">{g.business_name}</h3>
              <span
                className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${styleBadge[g.style] ?? styleBadge.dark}`}
              >
                {g.style}
              </span>
            </div>
            <p className="mt-2 line-clamp-2 flex-1 text-sm text-slate-400">{g.description}</p>
            <p className="mt-3 text-xs text-slate-500">
              {g.language} · {new Date(g.created_at).toLocaleDateString('en-GB')}
            </p>
            <div className="mt-4 flex gap-2 text-sm">
              <Link
                to={`/preview/${g.id}`}
                className="flex-1 rounded-lg bg-accent/15 py-2 text-center font-semibold text-accent-soft transition hover:bg-accent/25"
              >
                Preview
              </Link>
              <button
                onClick={() => downloadZip(g.id, g.business_name)}
                className="rounded-lg border border-line px-3 py-2 text-slate-300 transition hover:border-slate-500 hover:text-white"
                title="Download ZIP"
              >
                ⤓
              </button>
              <button
                onClick={() => remove(g.id)}
                className="rounded-lg border border-line px-3 py-2 text-slate-400 transition hover:border-red-500/50 hover:text-red-400"
                title="Delete"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </Shell>
  )
}

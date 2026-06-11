import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, downloadZip } from '../api'
import Shell from '../components/Shell'

const WIDTHS = { desktop: '100%', tablet: '768px', mobile: '390px' }

export default function Preview() {
  const { id } = useParams()
  const [gen, setGen] = useState(null)
  const [error, setError] = useState('')
  const [device, setDevice] = useState('desktop')

  useEffect(() => {
    api(`/api/generations/${id}`).then(setGen).catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <Shell>
        <p className="text-red-400">{error}</p>
      </Shell>
    )
  }

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link to="/dashboard" className="text-sm text-slate-400 hover:text-white">
            ← Back to dashboard
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-white">{gen?.business_name ?? 'Loading…'}</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border border-line p-1 text-sm">
            {Object.keys(WIDTHS).map((d) => (
              <button
                key={d}
                onClick={() => setDevice(d)}
                className={`rounded-md px-3 py-1.5 capitalize transition ${
                  device === d ? 'bg-accent text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
          {gen && (
            <button
              onClick={() => downloadZip(gen.id, gen.business_name)}
              className="rounded-lg bg-accent px-5 py-2 font-semibold text-white transition hover:bg-accent-soft"
            >
              Download ZIP
            </button>
          )}
        </div>
      </div>

      <div className="mt-6 flex justify-center rounded-2xl border border-line bg-panel p-4">
        {gen ? (
          <iframe
            title="Landing page preview"
            srcDoc={gen.html}
            sandbox="allow-scripts"
            style={{ width: WIDTHS[device] }}
            className="h-[75vh] max-w-full rounded-lg border border-line bg-white transition-all"
          />
        ) : (
          <div className="flex h-[75vh] items-center justify-center text-slate-500">Loading…</div>
        )}
      </div>
    </Shell>
  )
}

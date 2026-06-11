import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, saveSession } from '../api'
import AuthCard from '../components/AuthCard'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      saveSession(await api('/api/auth/login', { method: 'POST', body: { email, password } }))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function tryDemo() {
    setError('')
    setBusy(true)
    try {
      saveSession(await api('/api/auth/demo', { method: 'POST' }))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const input =
    'w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-strong placeholder-faint outline-none transition focus:border-accent'

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Log in to your workspace"
      footer={
        <>
          No account?{' '}
          <Link to="/register" className="text-accent-soft hover:underline">
            Sign up
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={input}
        />
        <input
          type="password"
          required
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={input}
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded-lg bg-accent py-2.5 font-semibold text-white transition hover:bg-accent-soft disabled:opacity-50"
        >
          {busy ? 'Please wait…' : 'Log in'}
        </button>
      </form>
      <div className="my-4 flex items-center gap-3 text-xs text-faint">
        <span className="h-px flex-1 bg-line" />
        or
        <span className="h-px flex-1 bg-line" />
      </div>
      <button
        onClick={tryDemo}
        disabled={busy}
        className="w-full rounded-lg border border-line py-2.5 font-semibold text-body transition hover:border-dim hover:text-strong disabled:opacity-50"
      >
        Try demo — no sign-up
      </button>
    </AuthCard>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, saveSession } from '../api'
import AuthCard from '../components/AuthCard'

export default function Register() {
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
      saveSession(await api('/api/auth/register', { method: 'POST', body: { email, password } }))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const input =
    'w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-white placeholder-slate-500 outline-none transition focus:border-accent'

  return (
    <AuthCard
      title="Create account"
      subtitle="Start generating landing pages"
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="text-accent-soft hover:underline">
            Log in
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
          minLength={8}
          placeholder="Password (min 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={input}
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded-lg bg-accent py-2.5 font-semibold text-white transition hover:bg-accent-soft disabled:opacity-50"
        >
          {busy ? 'Please wait…' : 'Sign up'}
        </button>
      </form>
    </AuthCard>
  )
}

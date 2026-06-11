import { Link, useNavigate } from 'react-router-dom'
import { clearSession, getEmail } from '../api'

export default function Shell({ children }) {
  const navigate = useNavigate()
  const email = getEmail()

  function logout() {
    clearSession()
    navigate('/')
  }

  return (
    <div className="min-h-screen">
      <nav className="sticky top-0 z-10 border-b border-line bg-ink/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link to="/dashboard" className="text-lg font-bold text-white">
            Landing<span className="text-accent-soft">Studio</span>
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-slate-400 sm:inline">{email}</span>
            <button
              onClick={logout}
              className="rounded-lg border border-line px-3 py-1.5 text-slate-300 transition hover:border-slate-500 hover:text-white"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  )
}

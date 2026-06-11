import { Link } from 'react-router-dom'
import { getToken } from '../api'
import AnimatedBackground from '../components/AnimatedBackground'
import ThemeControls from '../components/ThemeControls'

const features = [
  {
    icon: '✦',
    title: 'AI-crafted copy & design',
    text: 'Describe your business — the AI asks smart clarifying questions, then writes copy and designs the page around your answers.',
  },
  {
    icon: '◫',
    title: 'Three distinct styles',
    text: 'Dark glassmorphism, light minimal or bold vibrant. Every page ships with animations, FAQ accordion and a contact form.',
  },
  {
    icon: '⤓',
    title: 'Own your code',
    text: 'Download a clean single-file HTML page with zero dependencies. Host it anywhere — no lock-in, no watermarks.',
  },
]

export default function Landing() {
  const startHref = getToken() ? '/dashboard' : '/register'

  return (
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground />

      <nav className="relative z-[1] mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
        <span className="text-lg font-bold text-strong">
          Landing<span className="text-accent-soft">Studio</span>
        </span>
        <div className="flex items-center gap-3 text-sm">
          <ThemeControls />
          <Link to="/login" className="px-3 py-1.5 text-body transition hover:text-strong">
            Log in
          </Link>
          <Link
            to="/register"
            className="rounded-lg bg-accent px-4 py-1.5 font-semibold text-white transition hover:opacity-90"
          >
            Sign up
          </Link>
        </div>
      </nav>

      <header className="relative z-[1] mx-auto max-w-3xl px-6 pb-20 pt-24 text-center">
        <h1 className="text-4xl font-extrabold leading-tight text-strong sm:text-6xl">
          Landing pages,
          <br />
          <span className="bg-gradient-to-r from-accent-soft to-cyan-500 bg-clip-text text-transparent">
            generated in a minute
          </span>
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-lg text-dim">
          Tell the AI about your business. Answer five questions. Get a polished, responsive,
          animated landing page you can download and host anywhere.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            to={startHref}
            className="rounded-xl bg-accent px-7 py-3 font-semibold text-white shadow-lg shadow-accent/30 transition hover:opacity-90"
          >
            Generate your page
          </Link>
          <Link
            to="/login"
            className="rounded-xl border border-line px-7 py-3 font-semibold text-body transition hover:border-dim hover:text-strong"
          >
            Try the demo
          </Link>
        </div>
      </header>

      <section className="relative z-[1] mx-auto grid max-w-5xl gap-6 px-6 pb-24 sm:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-line bg-panel/60 p-6 backdrop-blur transition hover:-translate-y-1"
          >
            <div className="text-2xl text-accent-soft">{f.icon}</div>
            <h3 className="mt-3 font-bold text-strong">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-dim">{f.text}</p>
          </div>
        ))}
      </section>

      <footer className="relative z-[1] border-t border-line py-8 text-center text-sm text-faint">
        LandingStudio — AI landing page generator · © 2026
      </footer>
    </div>
  )
}

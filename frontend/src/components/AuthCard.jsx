import { Link } from 'react-router-dom'
import AnimatedBackground from './AnimatedBackground'
import ThemeControls from './ThemeControls'

export default function AuthCard({ title, subtitle, children, footer }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <AnimatedBackground />
      <div className="absolute right-6 top-6 z-[1]">
        <ThemeControls />
      </div>
      <div className="relative z-[1] w-full max-w-md">
        <Link to="/" className="mb-8 block text-center text-xl font-bold text-strong">
          Landing<span className="text-accent-soft">Studio</span>
        </Link>
        <div className="rounded-2xl border border-line bg-panel p-8 shadow-2xl">
          <h1 className="text-2xl font-bold text-strong">{title}</h1>
          <p className="mb-6 mt-1 text-sm text-dim">{subtitle}</p>
          {children}
        </div>
        <div className="mt-4 text-center text-sm text-dim">{footer}</div>
      </div>
    </div>
  )
}

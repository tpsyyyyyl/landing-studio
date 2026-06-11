import useTheme, { SCHEMES } from '../useTheme'

const DOT_COLORS = { indigo: '#6366f1', sunset: '#f97316', emerald: '#10b981' }

export default function ThemeControls() {
  const { theme, scheme, toggleTheme, setScheme } = useTheme()

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-2 rounded-full border border-line px-2.5 py-2">
        {SCHEMES.map((s) => (
          <button
            key={s}
            onClick={() => setScheme(s)}
            title={`${s} background`}
            style={{ background: DOT_COLORS[s] }}
            className={`h-3.5 w-3.5 rounded-full transition ${
              scheme === s ? 'scale-125 ring-2 ring-line' : 'opacity-40 hover:opacity-100'
            }`}
          />
        ))}
      </div>
      <button
        onClick={toggleTheme}
        title="Toggle light/dark theme"
        className="flex h-8 w-8 items-center justify-center rounded-full border border-line text-dim transition hover:text-strong"
      >
        {theme === 'dark' ? '☀' : '☾'}
      </button>
    </div>
  )
}

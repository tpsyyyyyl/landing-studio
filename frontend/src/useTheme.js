import { useEffect, useState } from 'react'

const THEME_KEY = 'landing_studio_theme'
const SCHEME_KEY = 'landing_studio_scheme'

export const SCHEMES = ['indigo', 'sunset', 'emerald']

export function applyStoredTheme() {
  const root = document.documentElement
  root.dataset.theme = localStorage.getItem(THEME_KEY) || 'dark'
  root.dataset.scheme = localStorage.getItem(SCHEME_KEY) || 'indigo'
}

export default function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || 'dark')
  const [scheme, setScheme] = useState(() => localStorage.getItem(SCHEME_KEY) || 'indigo')

  useEffect(() => {
    localStorage.setItem(THEME_KEY, theme)
    localStorage.setItem(SCHEME_KEY, scheme)
    document.documentElement.dataset.theme = theme
    document.documentElement.dataset.scheme = scheme
  }, [theme, scheme])

  return {
    theme,
    scheme,
    toggleTheme: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')),
    setScheme,
  }
}

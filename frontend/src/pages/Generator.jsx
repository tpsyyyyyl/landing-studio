import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import Shell from '../components/Shell'

const STYLES = [
  { id: 'dark', name: 'Dark Glass', text: 'Deep navy, glassmorphism cards, glowing accents' },
  { id: 'light', name: 'Light Minimal', text: 'Airy whitespace, clean borders, one muted accent' },
  { id: 'vibrant', name: 'Bold Vibrant', text: 'Saturated gradients, oversized type, pill buttons' },
]

const LANGUAGES = ['English', 'Ukrainian', 'German', 'Polish', 'Spanish']

export default function Generator() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const [businessName, setBusinessName] = useState('')
  const [description, setDescription] = useState('')
  const [style, setStyle] = useState('dark')
  const [language, setLanguage] = useState('English')
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState([])

  async function toQuestions(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const data = await api('/api/clarify', {
        method: 'POST',
        body: { business_name: businessName, description },
      })
      setQuestions(data.questions)
      setAnswers(data.questions.map(() => ''))
      setStep(2)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function generate() {
    setError('')
    setBusy(true)
    setStep(3)
    try {
      const answersText = questions
        .map((q, i) => (answers[i].trim() ? `${q} — ${answers[i].trim()}` : null))
        .filter(Boolean)
        .join('\n')
      const gen = await api('/api/generate', {
        method: 'POST',
        body: {
          business_name: businessName,
          description,
          answers: answersText,
          style,
          language,
        },
      })
      navigate(`/preview/${gen.id}`)
    } catch (err) {
      setError(err.message)
      setStep(2)
    } finally {
      setBusy(false)
    }
  }

  const input =
    'w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-strong placeholder-faint outline-none transition focus:border-accent'

  return (
    <Shell>
      <div className="mx-auto max-w-2xl">
        <div className="mb-8 flex items-center gap-3 text-sm">
          {['Business', 'Details', 'Generate'].map((label, i) => (
            <div key={label} className="flex items-center gap-3">
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                  step > i ? 'bg-accent text-white' : 'border border-line text-faint'
                }`}
              >
                {i + 1}
              </span>
              <span className={step > i ? 'text-strong' : 'text-faint'}>{label}</span>
              {i < 2 && <span className="h-px w-8 bg-line" />}
            </div>
          ))}
        </div>

        {step === 1 && (
          <form onSubmit={toQuestions} className="space-y-5">
            <h1 className="text-2xl font-bold text-strong">Tell us about your business</h1>
            <input
              required
              placeholder="Business name"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              className={input}
            />
            <textarea
              required
              rows={4}
              placeholder="What do you do? Who are your customers? What makes you different?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={input}
            />

            <div>
              <p className="mb-3 text-sm font-semibold text-body">Visual style</p>
              <div className="grid gap-3 sm:grid-cols-3">
                {STYLES.map((s) => (
                  <button
                    type="button"
                    key={s.id}
                    onClick={() => setStyle(s.id)}
                    className={`rounded-xl border p-4 text-left transition ${
                      style === s.id
                        ? 'border-accent bg-accent/10'
                        : 'border-line bg-panel hover:border-dim'
                    }`}
                  >
                    <p className="font-bold text-strong">{s.name}</p>
                    <p className="mt-1 text-xs text-dim">{s.text}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold text-body">Page language</p>
              <select value={language} onChange={(e) => setLanguage(e.target.value)} className={input}>
                {LANGUAGES.map((l) => (
                  <option key={l} value={l} className="bg-panel">
                    {l}
                  </option>
                ))}
              </select>
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}
            <button
              disabled={busy}
              className="w-full rounded-xl bg-accent py-3 font-semibold text-white transition hover:bg-accent-soft disabled:opacity-50"
            >
              {busy ? 'Asking the AI…' : 'Continue'}
            </button>
          </form>
        )}

        {step === 2 && (
          <div className="space-y-5">
            <h1 className="text-2xl font-bold text-strong">A few quick questions</h1>
            <p className="text-sm text-dim">
              Answers are optional but make the result much better.
            </p>
            {questions.map((q, i) => (
              <div key={i}>
                <p className="mb-1.5 text-sm text-body">{q}</p>
                <input
                  value={answers[i]}
                  onChange={(e) =>
                    setAnswers(answers.map((a, j) => (j === i ? e.target.value : a)))
                  }
                  placeholder="Your answer (optional)"
                  className={input}
                />
              </div>
            ))}
            {error && <p className="text-sm text-red-400">{error}</p>}
            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="rounded-xl border border-line px-6 py-3 font-semibold text-body transition hover:border-dim hover:text-strong"
              >
                Back
              </button>
              <button
                onClick={generate}
                disabled={busy}
                className="flex-1 rounded-xl bg-accent py-3 font-semibold text-white transition hover:bg-accent-soft disabled:opacity-50"
              >
                Generate landing page
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="py-24 text-center">
            <div className="mx-auto h-12 w-12 animate-spin rounded-full border-2 border-line border-t-accent" />
            <h1 className="mt-6 text-xl font-bold text-strong">Generating your page…</h1>
            <p className="mt-2 text-sm text-dim">
              The AI is writing copy and styling sections. Usually takes 20–60 seconds.
            </p>
          </div>
        )}
      </div>
    </Shell>
  )
}

# Landing Studio

AI-powered SaaS that generates complete, animated, responsive landing pages from a short business description — with accounts, generation history and one-click code export.

![Home](docs/home.png)

## How it works

1. **Describe your business** — name, what you do, pick one of 3 visual styles and the page language.
2. **Answer 5 AI questions** — the AI asks clarifying questions about your audience, tone and goals (all optional).
3. **Get your page** — a polished single-file HTML landing with animations, FAQ accordion and contact form. Preview it on desktop/tablet/mobile and download as ZIP.

| Dashboard | Generator wizard | Preview |
|---|---|---|
| ![Dashboard](docs/dashboard.png) | ![Generator](docs/generator.png) | ![Preview](docs/preview.png) |

| Light theme | Light + sunset scheme |
|---|---|
| ![Light theme](docs/home-light.png) | ![Sunset scheme](docs/dashboard-light.png) |

## Features

- **Auth & workspaces** — email/password accounts (bcrypt + JWT), every user sees only their own pages
- **Animated aurora background** — pure-CSS floating gradient orbs (zero image weight), with dark/light theme toggle and 3 selectable color schemes (indigo / sunset / emerald), persisted per user in localStorage
- **Demo mode** — "Try demo" button logs into a pre-seeded account, no sign-up needed
- **3 visual styles** — dark glassmorphism, light minimal, bold vibrant
- **Any language** — UI in English, generated pages in English, Ukrainian, German, Polish, Spanish…
- **Generation history** — every page is saved; re-open, preview, download or delete anytime
- **Code export** — download a clean, dependency-free single HTML file as ZIP
- **Responsive preview** — desktop / tablet / mobile toggle in an embedded sandbox

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy 2 (SQLite), PyJWT, bcrypt |
| AI | Groq — `llama-3.3-70b-versatile` |
| Frontend | React 19, Vite, Tailwind CSS 4, React Router |
| Tests | pytest (12 tests: auth, generations CRUD, access isolation) |
| Deploy | Render (single service: FastAPI serves the built SPA) |

## Run locally

```bash
# backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your free Groq key: https://console.groq.com
python -m backend.seed_demo   # creates the demo account
uvicorn backend.main:app --port 8011

# frontend (dev mode, in another terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173, proxies /api to :8011
```

For a production-style run, build the SPA and let FastAPI serve it:

```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app --port 8011   # http://localhost:8011
```

## Tests

```bash
python -m pytest tests/
```

AI calls are mocked in tests — no API key or tokens needed.

## API overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` · `/login` · `/demo` | Get a JWT |
| GET | `/api/auth/me` | Current user |
| POST | `/api/clarify` | 5 AI clarifying questions |
| POST | `/api/generate` | Generate & save a landing page |
| GET/DELETE | `/api/generations[/{id}]` | History CRUD |
| GET | `/api/generations/{id}/download` | ZIP export |

## Notes

- SQLite keeps the stack zero-config; the SQLAlchemy layer makes a later Postgres swap trivial.
- On Render's free tier the filesystem is ephemeral — the demo account is re-seeded on every restart.

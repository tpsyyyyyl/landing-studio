# HANDOFF — Landing Studio (де саме зупинились)

> Стан на **2026-06-11**, кінець сесії (вичерпано ліміт безкоштовного Fable 5).
> Це точка відновлення: відкрий цей файл у новій сесії — і продовжуй рівно звідси.
> Вікно безкоштовного Fable 5 діє **до 22.06.2026**.

## Проєкт
- **Landing Studio** — AI-SaaS, що генерує цілі лендінги (auth, БД, дашборд, історія, ZIP).
- Стек: FastAPI + SQLAlchemy 2 + Alembic (SQLite локально / Postgres на проді) · React 19 + Vite + Tailwind 4 · Groq AI.
- Директорія: `/home/bohdan/study/landing-studio/`
- venv: `/home/bohdan/study/.venv/` (Python 3.14)
- Локальний сервер: порт **8011**
- GitHub: `tpsyyyyyl/landing-studio` (публічний). Коміти/пуш — через `git`/`gh` CLI (github MCP видалили, він не потрібен).
- Мова відповідей: **тільки українська**.

## ⚠️ Незакомічені зміни (НЕ запушені!)
У робочому дереві лежать правки, які треба закомітити й запушити:
- `frontend/src/index.css` — фікс скролбарів (див. нижче)
- `backend/ai.py` — інструкція в промпт про `color-scheme` + стилізацію скролбара в генерованих сторінках
- `backend/main.py` — фікс path traversal у SPA-fallback

Перевірка перед комітом (обидві мають бути зелені):
```bash
cd /home/bohdan/study/landing-studio
/home/bohdan/study/.venv/bin/python -m pytest tests/ -q      # 20 passed
cd frontend && npm run build                                  # ✓ built
```
Останній стан: **20/20 тестів зелені, білд чистий.**

Коміт (приклад):
```bash
cd /home/bohdan/study/landing-studio
git add backend/ai.py backend/main.py frontend/src/index.css
git commit -m "Fix theme-aware scrollbars, SPA path traversal, scrollbar prompt"
git push
```

## Що зробили в цій сесії
1. **Скарга користувача:** некрасиві білі скролбари (скрін).
   - `index.css`: додав `color-scheme: dark/light` на `:root` і `[data-theme='light']`; тонкі скролбари через `scrollbar-width`/`scrollbar-color` + `::-webkit-scrollbar*`, колір з тем-змінних (`--t-faint`/`--t-dim`), прозорий трек, заокруглений палець.
   - `ai.py`: у промпт генерації додав вимогу ставити `color-scheme` на `:root` згенерованої сторінки + стилізувати її скролбар (щоб у згенерованих лендінгах теж не було білих смуг).
2. **Запустили `/code-review`** (high effort, 7 кутів). Результати — нижче.
3. **Виправили одразу (бо деплой публічний):**
   - 🔴 **Path traversal** у `backend/main.py` SPA-fallback: `os.path.join(_dist, path)` віддавав файли поза `dist/` (напр. `.env`, БД) через `../`. Закрив перевіркою `realpath` усередині `dist/`.
   - Прибрав дубль `border`/`background-clip` у `::-webkit-scrollbar-thumb:hover` (мій же код).

## 📋 Знахідки code-review — ТРІАЖ (звідси продовжити)
Виправлено: ✅ path traversal.
Залишилось вирішити з користувачем, що чіпати (від важливого до косметики):

**Варті уваги:**
- `auth.py:16` — `JWT_SECRET` має дефолт-заглушку. На нашому Render безпечно (`render.yaml` має `generateValue: true`), але варто додати startup-перевірку, щоб прод не стартував на відомому секреті. **Medium.**
- `routes_generations.py:178` — `list_generations` тягне всю колонку `html` (десятки КБ × N рядків), хоч `_summary()` її викидає. Легкий виграш: вибирати лише потрібні колонки (`load_only`/колонковий запит). **Medium, easy.**
- `routes_generations.py:65` — ліміт генерацій: COUNT-потім-INSERT не атомарний (TOCTOU). Паралельні запити можуть проскочити ліміт на кілька штук. Для портфоліо — низький пріоритет. **Low.**
- `models.py:19` + `routes:66` — `utcnow()` повертає aware-datetime, а колонки `DateTime` naive; біля півночі лічильник може зміщуватись, дати на фронті без `Z` парсяться як локальні. **Low/medium.**
- `auth.py:55` — `int(payload["sub"])` без guard → 500 замість 401, якщо валідний за підписом токен без `sub`. **Low.**
- `main.py:22` — подвійне керування схемою: `Base.metadata.create_all` + Alembic. На свіжій Postgres ок, але нова колонка в `models.py` без міграції розійдеться з мігрованою продакшн-БД. **Maintainability.**

**Косметика/REFUTED (швидше за все не чіпати):**
- bcrypt у sync-роутах — НЕ блокує event loop (роути `def`, не `async`). Refuted.
- Універсальний `*` для скролбара НЕ протікає в iframe прев'ю (окремий документ). Refuted.
- Дубль className `input` у Login/Register/Generator; різні regex для slug (api.js vs бекенд); зайвий `charCount` стейт; мертвий файл `components/AnimatedBackground.jsx`; `_map_error` віддає `str(e)` клієнту; демо-ліміт по рядку email замість прапора; `GENERATION_MAX_TOKENS` як паралельний dict до `MODELS`.

## 🚀 Головний відкритий крок: ДЕПЛОЙ на Fly.io (безкоштовно)

**Render відпав** — у 2024 році вони прибрали безкоштовний tier для web services, мінімум $7/місяць.
**Обрали Fly.io** — є справжній безкоштовний tier (256MB RAM, shared CPU).

### Що треба зробити в наступній сесії:
1. Встановити Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Залогінитись: `fly auth login`
3. Створити `fly.toml` у корені проєкту (ще не створено — треба налаштувати)
4. Для БД: використати **Fly Postgres** (безкоштовно в межах free allowance) або **Supabase** (щедріший безкоштовний Postgres)
5. Задеплоїти: `fly deploy`

### Змінні середовища для Fly:
```
GROQ_API_KEY=<твій ключ з console.groq.com>
JWT_SECRET=<згенерувати: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=<буде після створення Fly Postgres>
```

### Після деплою:
- перевірити прод: `/api/health`, демо-логін, реальна генерація;
- додати живе посилання в `README.md`;
- закомітити + запушити.

> `render.yaml` можна залишити в репо — не заважає.

## Деталі Groq (щоб не наступити вдруге)
- Моделі: `gpt-oss` = `openai/gpt-oss-120b` (дефолт, якість), `scout` = `meta-llama/llama-4-scout-17b-16e-instruct` (швидкість). Maverick задеприкейчена на Groq (02.2026).
- Безкоштовний tier: **8000 TPM на запит** для gpt-oss → `GENERATION_MAX_TOKENS["gpt-oss"]=6000` (лишити місце на промпт). Перевищення → 413.
- Денні ліміти в застосунку: 20/користувача, 5/демо (захищають ключ).
- Демо-акаунт: `demo@landing.studio` / `demo1234`.

## Obsidian
В кінці сесії зберегти ключові нотатки у `/home/bohdan/Im clown/нотатки/` (формат `YYYY-MM-DD - тема.md`). Нотатка про збірку SaaS уже є; варто дописати про скролбари/тему/бекенд-апгрейд і деплой, коли завершимо.

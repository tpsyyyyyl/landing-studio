// One-off helper: takes README screenshots against a running local server.
// Usage: node scripts/screenshots.mjs
import puppeteer from 'puppeteer-core'

const BASE = 'http://localhost:8011'
const OUT = new URL('../../docs/', import.meta.url).pathname

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome',
  args: ['--no-sandbox', '--hide-scrollbars'],
})
const page = await browser.newPage()
await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 })

async function shot(path, name, wait = 800) {
  await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, wait))
  await page.screenshot({ path: `${OUT}${name}.png` })
  console.log(`saved ${name}.png`)
}

await shot('/', 'home')
await shot('/login', 'login')

// log into the demo account, then authenticated pages
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle0' })
const session = await page.evaluate(async () => {
  const res = await fetch('/api/auth/demo', { method: 'POST' })
  return res.json()
})
await page.evaluate((s) => {
  localStorage.setItem('landing_studio_token', s.token)
  localStorage.setItem('landing_studio_email', s.email)
}, session)

await shot('/dashboard', 'dashboard')
await shot('/new', 'generator')

const gens = await page.evaluate(async () => {
  const res = await fetch('/api/generations', {
    headers: { Authorization: `Bearer ${localStorage.getItem('landing_studio_token')}` },
  })
  return res.json()
})
if (gens.length) await shot(`/preview/${gens[gens.length - 1].id}`, 'preview', 1500)

await browser.close()

import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'

import { API_URL, ApiError, compareText, type Comparison, type Prediction } from './api'

const MAX_LENGTH = 2000
const NAV_ITEMS = [
  { id: 'periksa', label: 'Periksa' },
  { id: 'model', label: 'Model' },
  { id: 'catatan', label: 'Catatan' },
] as const

const EXAMPLES = [
  { label: 'Hinaan langsung', text: 'Dasar bodoh, tulisanmu jelek banget.' },
  { label: 'Sindiran', text: 'Wah pintar sekali, sampai salah dua kali.' },
  { label: 'Percakapan biasa', text: 'Semangat terus, besok pasti lebih baik!' },
] as const

type Theme = 'light' | 'dark'

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function MenuIcon({ open }: { open: boolean }) {
  return open ? (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ) : (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

function ThemeToggle({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  const dark = theme === 'dark'
  return (
    <button
      type="button"
      className="icon-button theme-toggle"
      onClick={onToggle}
      role="switch"
      aria-checked={dark}
      aria-label={dark ? 'Gunakan tema terang' : 'Gunakan tema gelap'}
      title={dark ? 'Tema terang' : 'Tema gelap'}
    >
      {dark ? <SunIcon /> : <MoonIcon />}
    </button>
  )
}

function ResultPanel({
  model,
  subtitle,
  result,
}: {
  model: string
  subtitle: string
  result: Prediction
}) {
  const percent = Math.round(result.bully_probability * 100)
  const isBully = result.label === 'bully'

  return (
    <article className="model-panel" aria-label={`${model}: ${isBully ? 'bully' : 'non-bully'}`}>
      <div className="panel-head">
        <div>
          <h3 className="panel-title">{model}</h3>
          <p className="panel-subtitle">{subtitle}</p>
        </div>
        <span className="badge">{isBully ? 'Bully' : 'Non-bully'}</span>
      </div>

      <p className="probability">
        {percent}
        <span className="probability-unit">%</span>
      </p>
      <p className="probability-label">probabilitas bully</p>

      <div
        className="meter"
        role="img"
        aria-label={`${model}: probabilitas kelas bully ${percent} persen`}
      >
        <span className="meter-fill" style={{ width: `${percent}%` }} />
      </div>

      <dl className="panel-meta">
        <div>
          <dt>Ambang</dt>
          <dd>{Math.round(result.threshold * 100)}%</dd>
        </div>
        <div>
          <dt>Keyakinan</dt>
          <dd>{Math.round(result.score * 100)}%</dd>
        </div>
      </dl>

      <p className="panel-note">
        Label mengikuti ambang model. Angka adalah probabilitas kelas bully, bukan
        kepastian pelanggaran.
      </p>
    </article>
  )
}

function ComparisonView({ comparison }: { comparison: Comparison }) {
  const delta = Math.round(
    (comparison.b.bully_probability - comparison.a.bully_probability) * 100,
  )

  return (
    <div className="compare-wrap" aria-live="polite">
      <div className="compare-grid">
        <ResultPanel model="Model A" subtitle="Data asli" result={comparison.a} />
        <ResultPanel
          model="Model B"
          subtitle="Data asli + sintetis"
          result={comparison.b}
        />
      </div>
      <p className="compare-delta">
        Selisih probabilitas B dan A: {delta > 0 ? '+' : ''}
        {delta} poin
      </p>
      <p className="compare-note">
        Model B adalah eksperimen augmentasi sintetis. Selisih pada satu teks bukan
        bukti bahwa B lebih baik. Gunakan metrik validation dan test.
      </p>
    </div>
  )
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() =>
    document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
  )
  const [text, setText] = useState('')
  const [comparison, setComparison] = useState<Comparison | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('periksa')

  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const resultRef = useRef<HTMLDivElement | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    document.body.classList.toggle('menu-open', menuOpen)
    return () => document.body.classList.remove('menu-open')
  }, [menuOpen])

  useEffect(() => () => controllerRef.current?.abort(), [])

  useEffect(() => {
    if (!comparison || !resultRef.current) {
      return
    }
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resultRef.current.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'start',
    })
  }, [comparison])

  const canSubmit = text.trim().length > 0 && text.length <= MAX_LENGTH && !isLoading

  async function compare() {
    const trimmed = text.trim()
    if (!trimmed || trimmed.length > MAX_LENGTH || isLoading) {
      return
    }

    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setIsLoading(true)
    setError(null)

    try {
      const result = await compareText(trimmed, controller.signal)
      setComparison(result)
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === 'AbortError') {
        return
      }
      setComparison(null)
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Terjadi kesalahan tak terduga. Coba lagi.',
      )
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null
        setIsLoading(false)
      }
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void compare()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault()
      void compare()
    }
  }

  function handleChange(value: string) {
    setText(value)
    if (!isLoading) {
      setComparison(null)
      setError(null)
    }
  }

  function applyExample(value: string) {
    setText(value)
    setComparison(null)
    setError(null)
    textareaRef.current?.focus()
  }

  function navigate(id: string) {
    setActiveSection(id)
    setMenuOpen(false)
  }

  return (
    <>
      <a className="skip-link" href="#content">
        Lewati ke konten
      </a>

      <aside className="sidebar" aria-label="Navigasi utama">
        <ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
        <p className="sidebar-brand">CyberBully</p>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={`nav-button ${activeSection === item.id ? 'is-active' : ''}`}
              onClick={() => navigate(item.id)}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <footer className="sidebar-footer">
          <a href="https://github.com/Rbooii/CyberBully-Detection" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={API_URL} target="_blank" rel="noreferrer">
            API
          </a>
          <span>2026</span>
        </footer>
      </aside>

      <header className="mobile-bar">
        <span className="mobile-brand">CyberBully</span>
        <div className="mobile-controls">
          <ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
          <button
            type="button"
            className="icon-button menu-toggle"
            aria-label={menuOpen ? 'Tutup menu' : 'Buka menu'}
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <MenuIcon open={menuOpen} />
          </button>
        </div>
      </header>

      {menuOpen ? (
        <div className="mobile-drawer" id="mobile-menu">
          <nav aria-label="Navigasi mobile">
            {NAV_ITEMS.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                className={`nav-button ${activeSection === item.id ? 'is-active' : ''}`}
                onClick={() => navigate(item.id)}
              >
                {item.label}
              </a>
            ))}
          </nav>
          <div className="drawer-footer">
            <a href="https://github.com/Rbooii/CyberBully-Detection" target="_blank" rel="noreferrer">
              GitHub
            </a>
            <a href={API_URL} target="_blank" rel="noreferrer">
              API
            </a>
          </div>
        </div>
      ) : null}

      <main id="content" className="page-shell">
        <section id="periksa" className="hero">
          <h1>Bandingkan dua model pada teks yang sama.</h1>
          <p className="hero-deck">
            Model A dilatih hanya pada komentar asli. Model B dilatih pada data asli
            ditambah 20.000 contoh sintetis. Keduanya diuji pada validation dan test
            yang sama.
          </p>
          <div className="meta-row">
            <span>Model A 10.397 baris</span>
            <span>Model B 30.397 baris</span>
            <span>Validation 1.300 baris</span>
          </div>
        </section>

        <section className="checker" aria-labelledby="checker-title">
          <h2 id="checker-title" className="section-title">
            Periksa teks
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="field-row">
              <label htmlFor="comment">Teks yang diperiksa</label>
              <span className="counter">
                {text.length} / {MAX_LENGTH}
              </span>
            </div>
            <textarea
              id="comment"
              ref={textareaRef}
              value={text}
              onChange={(event) => handleChange(event.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={MAX_LENGTH}
              rows={6}
              placeholder="Tulis atau tempel satu komentar di sini."
              spellCheck={false}
            />
            <div className="actions">
              <button className="ink-button" type="submit" disabled={!canSubmit}>
                {isLoading ? 'Membandingkan' : 'Bandingkan teks'}
              </button>
              <span className="shortcut">Ctrl atau Cmd dan Enter</span>
            </div>
          </form>

          <div className="examples" aria-label="Contoh teks">
            <span className="examples-label">Coba contoh</span>
            {EXAMPLES.map((example) => (
              <button
                key={example.label}
                type="button"
                className="example-button"
                title={example.text}
                onClick={() => applyExample(example.text)}
              >
                {example.label}
              </button>
            ))}
          </div>
        </section>

        <section id="model" className="result-section" aria-labelledby="result-title">
          <h2 id="result-title" className="section-title">
            Hasil
          </h2>
          <div className="result-zone" ref={resultRef}>
            {error ? (
              <p className="notice" role="alert">
                {error}
              </p>
            ) : null}

            {comparison ? <ComparisonView comparison={comparison} /> : null}

            {isLoading ? (
              <p className="idle-note" role="status">
                Membandingkan kedua model
              </p>
            ) : null}

            {!comparison && !error && !isLoading ? (
              <p className="idle-note">
                Hasil Model A dan B muncul di sini setelah teks diperiksa.
              </p>
            ) : null}
          </div>
        </section>

        <section id="catatan" className="notes" aria-labelledby="notes-title">
          <h2 id="notes-title" className="section-title">
            Catatan
          </h2>
          <p>
            Data sintetis hanya masuk train. Validation dan test memakai komentar
            asli, sehingga perbandingan tidak menilai hafalan template.
          </p>
          <p>
            Model tidak memahami konteks percakapan, sindiran halus, atau hubungan
            antar pengguna. Gunakan hasil ini sebagai bahan pertimbangan, bukan
            putusan otomatis.
          </p>
          <p className="mono-note">
            Dataset Ibrohim dan Budi, 2019. Lisensi CC BY-NC-SA 4.0.
          </p>
        </section>

        <footer className="site-footer">
          <span>CyberBully 2026</span>
          <div className="footer-links">
            <a href="https://github.com/Rbooii/CyberBully-Detection" target="_blank" rel="noreferrer">
              GitHub
            </a>
            <a href={`${API_URL}/health`} target="_blank" rel="noreferrer">
              Status API
            </a>
          </div>
        </footer>
      </main>
    </>
  )
}

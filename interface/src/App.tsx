import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'

import { API_URL, ApiError, predictText, type Prediction } from './api'

const MAX_LENGTH = 2000

const EXAMPLES = [
  { label: 'Hinaan langsung', text: 'Dasar bodoh, tulisanmu jelek banget.' },
  { label: 'Sindiran', text: 'Wah pintar sekali, sampai salah dua kali.' },
  { label: 'Percakapan biasa', text: 'Semangat terus, besok pasti lebih baik!' },
] as const

function ResultPanel({ result }: { result: Prediction }) {
  const percent = Math.round(result.bully_probability * 100)
  const isBully = result.label === 'bully'

  return (
    <article className={`verdict ${isBully ? 'is-bully' : 'is-safe'}`} aria-live="polite">
      <div className="verdict-head">
        <div>
          <p className="verdict-context">Hasil pembacaan</p>
          <h2 className="verdict-title">
            {isBully ? 'Cenderung bully' : 'Cenderung non-bully'}
          </h2>
        </div>
        <p className="verdict-prob">
          <strong>{percent}</strong>
          <span>%</span>
          <small>probabilitas bully</small>
        </p>
      </div>

      <div
        className="meter"
        role="img"
        aria-label={`Probabilitas kelas bully ${percent} persen`}
      >
        <span className="meter-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="meter-scale" aria-hidden="true">
        <span>0%</span>
        <span>100%</span>
      </div>

      <p className="fineprint">
        Label mengikuti ambang model. Angka di atas adalah probabilitas kelas bully,
        bukan kepastian bahwa komentar melanggar aturan.
      </p>
    </article>
  )
}

export default function App() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<Prediction | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const resultRef = useRef<HTMLDivElement | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => () => controllerRef.current?.abort(), [])

  useEffect(() => {
    if (!result || !resultRef.current) {
      return
    }
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resultRef.current.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'nearest',
    })
  }, [result])

  const canSubmit = text.trim().length > 0 && text.length <= MAX_LENGTH && !isLoading

  async function check() {
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
      const prediction = await predictText(trimmed, controller.signal)
      setResult(prediction)
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === 'AbortError') {
        return
      }
      setResult(null)
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
    void check()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault()
      void check()
    }
  }

  function handleChange(value: string) {
    setText(value)
    if (!isLoading) {
      setResult(null)
      setError(null)
    }
  }

  function applyExample(value: string) {
    setText(value)
    setResult(null)
    setError(null)
    textareaRef.current?.focus()
  }

  return (
    <div className="shell">
      <header className="masthead">
        <span className="wordmark">CyberBully</span>
        <span className="masthead-meta">Pemeriksa teks bahasa Indonesia</span>
      </header>

      <main className="layout">
        <section className="intro" aria-labelledby="page-title">
          <h1 id="page-title">
            Periksa satu komentar, lihat apa yang ditangkap model.
          </h1>
          <p className="deck">
            Model bahasa Indonesia membaca pola hinaan dan ujaran kebencian, lalu
            mengembalikan probabilitas. Bukan putusan otomatis, bukan pengganti
            konteks percakapan.
          </p>

          <dl className="facts">
            <div>
              <dt>Data latih</dt>
              <dd>12.997 komentar</dd>
            </div>
            <div>
              <dt>Keluaran</dt>
              <dd>Probabilitas bully</dd>
            </div>
          </dl>

          <p className="intro-note">
            Sindiran halus, kata kasar yang akrab, dan percakapan panjang masih
            sering salah dibaca. Gunakan hasil ini sebagai bahan pertimbangan.
          </p>
        </section>

        <section className="workbench" aria-label="Pemeriksa teks">
          <form onSubmit={handleSubmit}>
            <div className="field-head">
              <label htmlFor="comment">Teks yang diperiksa</label>
              <span className="count">
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
              rows={7}
              placeholder="Tulis atau tempel satu komentar di sini."
              spellCheck={false}
            />

            <div className="actions">
              <button className="primary" type="submit" disabled={!canSubmit}>
                {isLoading ? 'Memeriksa…' : 'Periksa teks'}
              </button>
              <p className="shortcut">Ctrl/⌘ + Enter</p>
            </div>
          </form>

          <div className="examples" aria-label="Contoh teks">
            <span className="examples-label">Coba contoh</span>
            {EXAMPLES.map((example) => (
              <button
                key={example.label}
                type="button"
                className="example"
                title={example.text}
                onClick={() => applyExample(example.text)}
              >
                {example.label}
              </button>
            ))}
          </div>

          <div className="result-zone" ref={resultRef}>
            {error ? (
              <p className="notice" role="alert">
                {error}
              </p>
            ) : null}

            {result ? <ResultPanel result={result} /> : null}

            {isLoading ? (
              <p className="idle-note" role="status">
                Membaca teks…
              </p>
            ) : null}

            {!result && !error && !isLoading ? (
              <p className="idle-note">
                Hasil akan muncul di sini setelah teks diperiksa.
              </p>
            ) : null}
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>
          Model dilatih pada 12.997 komentar berbahasa Indonesia. Dataset Ibrohim
          &amp; Budi (2019), CC BY-NC-SA 4.0.
        </p>
        <p>
          Hasil adalah probabilitas, bukan putusan. Konteks percakapan, sindiran
          halus, dan hubungan antar pengguna tidak terbaca model.
        </p>
        <p className="api-line">API: {API_URL}</p>
      </footer>
    </div>
  )
}

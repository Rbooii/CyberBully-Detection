import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'

import { API_URL, ApiError, compareText, type Comparison, type Prediction } from './api'

const MAX_LENGTH = 2000

const EXAMPLES = [
  { label: 'Hinaan langsung', text: 'Dasar bodoh, tulisanmu jelek banget.' },
  { label: 'Sindiran', text: 'Wah pintar sekali, sampai salah dua kali.' },
  { label: 'Percakapan biasa', text: 'Semangat terus, besok pasti lebih baik!' },
] as const

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
    <article className={`model-panel ${isBully ? 'is-bully' : 'is-safe'}`}>
      <div className="model-head">
        <div>
          <h2 className="model-name">{model}</h2>
          <p className="model-sub">{subtitle}</p>
        </div>
        <p className="verdict-prob">
          <strong>{percent}</strong>
          <span>%</span>
          <small>probabilitas bully</small>
        </p>
      </div>

      <p className="verdict-context">Hasil pembacaan</p>
      <h3 className="verdict-title">
        {isBully ? 'Cenderung bully' : 'Cenderung non-bully'}
      </h3>

      <div
        className="meter"
        role="img"
        aria-label={`${model}: probabilitas kelas bully ${percent} persen`}
      >
        <span className="meter-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="meter-scale" aria-hidden="true">
        <span>0%</span>
        <span>100%</span>
      </div>

      <p className="fineprint">
        Label mengikuti ambang model ini. Angka adalah probabilitas kelas bully,
        bukan kepastian pelanggaran.
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
        Selisih probabilitas B − A: {delta > 0 ? '+' : ''}
        {delta} poin persentase.
      </p>
      <p className="compare-note">
        Model B adalah eksperimen augmentasi sintetis. Selisih pada satu teks bukan
        bukti bahwa B lebih baik; gunakan metrik validation dan test.
      </p>
    </div>
  )
}

export default function App() {
  const [text, setText] = useState('')
  const [comparison, setComparison] = useState<Comparison | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const resultRef = useRef<HTMLDivElement | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => () => controllerRef.current?.abort(), [])

  useEffect(() => {
    if (!comparison || !resultRef.current) {
      return
    }
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resultRef.current.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'nearest',
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

  return (
    <div className="shell">
      <header className="masthead">
        <span className="wordmark">CyberBully</span>
        <span className="masthead-meta">Pemeriksa teks bahasa Indonesia</span>
      </header>

      <main className="layout">
        <section className="intro" aria-labelledby="page-title">
          <h1 id="page-title">Bandingkan dua model pada teks yang sama.</h1>
          <p className="deck">
            Model A dilatih hanya pada komentar asli. Model B dilatih pada data
            asli ditambah 15.000 contoh sintetis. Keduanya diuji pada validation
            dan test yang sama.
          </p>

          <dl className="facts">
            <div>
              <dt>Model A</dt>
              <dd>Data asli</dd>
            </div>
            <div>
              <dt>Model B</dt>
              <dd>Asli + sintetis</dd>
            </div>
          </dl>

          <p className="intro-note">
            Data sintetis hanya masuk train. Validation dan test tetap komentar
            asli, sehingga perbandingan tidak menilai hafalan template.
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
                {isLoading ? 'Membandingkan…' : 'Bandingkan teks'}
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

            {comparison ? <ComparisonView comparison={comparison} /> : null}

            {isLoading ? (
              <p className="idle-note" role="status">
                Membandingkan kedua model…
              </p>
            ) : null}

            {!comparison && !error && !isLoading ? (
              <p className="idle-note">
                Hasil Model A dan B akan muncul di sini setelah teks diperiksa.
              </p>
            ) : null}
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>
          Model A: data asli. Model B: data asli + 15.000 contoh sintetis. Dataset
          Ibrohim &amp; Budi (2019), CC BY-NC-SA 4.0.
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

export type PredictionLabel = 'bully' | 'non-bully'

export interface Prediction {
  label: PredictionLabel
  score: number
  bully_probability: number
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

export async function predictText(
  text: string,
  signal: AbortSignal,
): Promise<Prediction> {
  let response: Response

  try {
    response = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new ApiError(
      `Tidak bisa menghubungi API di ${API_URL}. Pastikan server API berjalan.`,
      0,
    )
  }

  if (response.status === 503) {
    throw new ApiError(
      'Model belum tersedia. Jalankan training, lalu nyalakan ulang API.',
      503,
    )
  }

  if (response.status === 422) {
    throw new ApiError('Teks harus 1–2000 karakter dan tidak boleh kosong.', 422)
  }

  if (!response.ok) {
    throw new ApiError(`Permintaan gagal (${response.status}). Coba lagi.`, response.status)
  }

  return (await response.json()) as Prediction
}

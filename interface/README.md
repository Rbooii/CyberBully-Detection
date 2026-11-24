# Interface — CyberBully

Frontend demo untuk API deteksi cyberbullying. Vite + React + TypeScript strict.

## Menjalankan

```bash
cd interface
npm install
npm run dev
```

Buka <http://localhost:5173>. API harus berjalan di `http://localhost:8000`:

```bash
uvicorn api.main:app --reload
```

Jika API berada di alamat lain, buat `interface/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

Jangan memakai `VITE_API_URL` untuk menyimpan rahasia; semua variabel `VITE_*`
ikut ter-bundle ke browser.

## Perilaku

- Tombol `Periksa teks` mengirim `POST /predict` dengan `{ "text": ... }`.
- Hasil menampilkan label (`bully` / `non-bully`), probabilitas kelas bully, dan
  catatan bahwa label mengikuti ambang model.
- Model belum tersedia → pesan 503, bukan stack trace.
- API tidak bisa dihubungi → pesan koneksi dengan URL yang dipakai.
- Input kosong atau >2000 karakter dicegah di UI dan divalidasi ulang API (422).
- CORS API hanya mengizinkan `http://localhost:5173` dan `http://127.0.0.1:5173`.

## Verifikasi

```bash
npm run typecheck
npm run build
npm run lint
```

`node_modules/` dan `dist/` tidak di-commit.

## Catatan

Ini alat bantu moderasi, bukan penghukum otomatis. Dataset berlisensi
CC BY-NC-SA 4.0; demo untuk riset/edukasi.

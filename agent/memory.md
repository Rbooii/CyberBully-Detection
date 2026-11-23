# Memory — CyberBully

Log keputusan dan status untuk sesi agent berikutnya. Append-only, entri terbaru
di bawah. Aturan kerja ada di `agents.md`, cara operasional di `agent/skills.md`.

## 2026-11-23 — Audit environment & scaffold awal

**Keputusan**

- `ml-lab` = venv buatan uv di `/Users/arcozkwn/.venvs/ml`, Python 3.12.16.
  Bukan conda/pyenv: keduanya tidak terpasang.
- Frontend akan berada di `interface/` (Vite + React + TS), menggantikan
  `frontend/` yang tertulis di `agents.md` §3/§4/§10.
- Dokumentasi agent memakai dua file datar: `agent/skills.md` + `agent/memory.md`.

**Alasan**

- Path env ditemukan lewat kernelspec Jupyter "Python (ML Lab)"; tidak ada di
  PATH sehingga `conda env list`/`pyenv versions` tidak menemukannya.
- Folder `frontend/` tidak pernah dibuat; pemilik repo meminta `interface/`
  khusus untuk implementasi frontend ringan.
- Dua file datar lebih mudah dirawat daripada subfolder kosong
  `agent/skills/` dan `agent/memory/` yang sebelumnya ada.

**Bukti**

- Python 3.12.16, torch 2.15.0, MPS `available=True`, matmul MPS berhasil.
- Instalasi `.[api,dev]` menarik transformers 5.24.0, datasets, accelerate,
  fastapi 0.165.0, pytest 9.2.0.
- `python -m pytest`: 12 passed in 0.74s.
- Smoke test CLI: CSV sintetis 42 baris → 40 setelah dedup → train 32 / val 4 /
  test 4, tiap split memuat kedua kelas.

**Terbuka / belum terverifikasi**

- Belum ada dataset asli dan `data/eval/implicit_eval.csv`; belum ada
  `train.py`, `evaluate.py`, `predict.py`, API, maupun frontend.
- Dedup masih exact setelah normalisasi. Teks "nyaris sama" (typo, parafrase)
  belum dicegah; ini celah terhadap `agents.md` §6.1 yang perlu diputuskan
  pemilik (mis. MinHash/`difflib`).
- `notebooks/01_experiment.ipynb` masih 0 byte dan namanya tidak sesuai
  konvensi `NN_topik_snake_case.ipynb`.
- `agents.md` di root memakai huruf kecil, sedangkan §3 menulis `AGENTS.md`.
  Belum di-rename agar tidak memutus referensi yang ada.
- Transformers terpasang 5.24.0; kompatibilitas kode training (Trainer,
  tokenizer, `datasets`) belum diuji karena `train.py` belum ada.

**Langkah berikutnya**

1. Pilih dataset dan petakan label bersama pemilik, lalu jalankan
   `cyberbully.data` pada data asli.
2. Bangun `train.py` (HF Trainer, MPS) dan uji `--subset` kecil dulu.
3. Siapkan baseline TF-IDF + Logistic Regression sebelum menyimpulkan apa pun
   tentang IndoBERT.

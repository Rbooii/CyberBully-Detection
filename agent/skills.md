# Skills — CyberBully

Panduan operasional untuk agent. Aturan wajib tetap di `agents.md`; file ini
tidak menggantikannya dan tidak boleh dipakai untuk melonggarkan aturan.

## Environment (audit 2026-11-23)

- `ENV_TYPE=venv` (dibuat uv 0.13.8), `ENV_PATH=/Users/arcozkwn/.venvs/ml`
- `PYTHON=/Users/arcozkwn/.venvs/ml/bin/python` — Python 3.12.16, arm64
- Kernel Jupyter: "Python (ML Lab)" → `~/Library/Jupyter/kernels/ml/kernel.json`
- Tidak ada conda/pyenv di mesin ini. Jangan pakai Python Homebrew (3.15).
- Terpasang: torch 2.15.0 (MPS True), transformers 5.24.0, datasets,
  accelerate, scikit-learn 1.9.1, pandas 3.1.1, numpy 2.5.4,
  fastapi 0.165.0, pytest 9.2.0.

## Perintah

```bash
# install ulang paket proyek
uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"

# data
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.data \
    --input data/raw/<file>.csv --text-col <kolom> --label-col <kolom> \
    --positive <nilai_bully>

# test (addopts sudah -q; jangan tambah -q lagi)
/Users/arcozkwn/.venvs/ml/bin/python -m pytest
```

## Checklist MPS

- `export PYTORCH_ENABLE_MPS_FALLBACK=1`
- `dataloader_num_workers=0`, tanpa `fp16`
- mulai `batch_size=8–16`, `max_length=64–128`
- cek: `python -c "import torch; print(torch.backends.mps.is_available())"`

## Konvensi repo

- Frontend di `interface/` (Vite + React + TypeScript strict), bukan `frontend/`.
- `agent/skills.md` dan `agent/memory.md` di-commit; perbarui `memory.md` di
  akhir sesi.
- Semua path lewat `cyberbully.config`; jangan hardcode path absolut.

## Jebakan yang sudah terbukti

- **Dedup setelah normalisasi**: URL/mention diganti `<url>`/`<user>`, sehingga
  banyak komentar berbeda bisa kolaps jadi satu teks. Kalau split gagal dengan
  "tiap kelas butuh minimal 2 contoh", periksa dulu berapa baris yang hilang
  karena dedup — bisa jadi datanya memang terlalu seragam.
- **transformers 5.24.0**, bukan 4.x. API `Trainer`/tokenizer bisa berbeda dari
  contoh 4.x; baca signature sebelum menulis `train.py`.
- `pytest -q` akan menjadi `-qq` karena `addopts` di `pyproject.toml`; ringkasan
  hasil hilang.
- Nama file aturan di root adalah `agents.md` (huruf kecil), bukan `AGENTS.md`.
- Dedup yang ada hanya **exact setelah normalisasi**; near-duplicate fuzzy
  (mis. typo/parafrase) belum ditangani — lihat `memory.md`.

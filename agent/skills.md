# Skills — CyberBully

Panduan operasional untuk agent. Aturan wajib tetap di `agents.md`; file ini
tidak menggantikannya dan tidak boleh dipakai untuk melonggarkan aturan.

## Environment (audit 2026-11-23)

- `ENV_TYPE=venv` (dibuat uv 0.13.8), `ENV_PATH=/Users/arcozkwn/.venvs/ml`
- `PYTHON=/Users/arcozkwn/.venvs/ml/bin/python` — Python 3.12.16, arm64
- Kernel Jupyter: "Python (ML Lab)" → `~/Library/Jupyter/kernels/ml/kernel.json`
- Tidak ada conda/pyenv di mesin ini. Jangan pakai Python Homebrew (3.15).
- Terpasang: torch 2.15.0 (MPS True), transformers 5.24.0, datasets 5.2.0,
  accelerate, scikit-learn 1.9.1, pandas 3.1.1, numpy 2.5.4,
  fastapi 0.165.0, pytest 9.2.0, nbformat 5.11.1, nbclient 0.11.0.

## Perintah

```bash
# install ulang paket proyek
uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"

# data (dataset proyek)
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.data \
    --input data/raw/re_dataset.csv --text-col Tweet \
    --label-col HS Abusive --positive 1 --label-mode any \
    --keep-cols HS Abusive

# smoke training (wajib sebelum run penuh)
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 128 --epochs 1 --batch-size 8 --max-length 32 --out models/smoke

# evaluasi validation
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.evaluate --split val

# test (addopts sudah -q; jangan tambah -q lagi)
/Users/arcozkwn/.venvs/ml/bin/python -m pytest
```

## Colab

- Panduan: `docs/colab.md`; notebook `00_colab_setup` lalu `06_colab_training`.
- Device otomatis CUDA > MPS > CPU (`cyberbully.runtime.resolve_device`).
- Di T4 `fp16` otomatis aktif; workers 2; checkpoint ke Drive; lanjutkan `--resume`.
- Repo belum punya remote; pemilik push sendiri. Notebook punya opsi zip/Drive.

## Konvensi repo

- Frontend di `interface/` (Vite + React + TypeScript strict), bukan `frontend/`.
- `agent/skills.md` dan `agent/memory.md` di-commit; perbarui `memory.md` di
  akhir sesi.
- Semua path lewat `cyberbully.config`; jangan hardcode path absolut.
- Setiap notebook wajib: Tujuan, Prasyarat, Estimasi waktu, Glosarium, Ringkasan;
  setiap sel kode didahului markdown ≥120 karakter. Ditegakkan
  `tests/test_notebooks.py`.

## Jebakan yang sudah terbukti

- **transformers 5.24**, bukan 4.x:
  - `Trainer(tokenizer=...)` sudah diganti `processing_class=...`.
  - `evaluation_strategy` → `eval_strategy`.
  - `warmup_ratio` sudah tidak ada; hitung `warmup_steps` manual.
  - `save_safetensors` dan `group_by_length` sudah tidak ada.
- `prajjwal1/bert-tiny` tokenizernya gagal di transformers 5 (butuh
  sentencepiece/tiktoken). Untuk smoke pakai
  `hf-internal-testing/tiny-random-BertForSequenceClassification`; IndoBERT aman.
- **Dedup setelah normalisasi**: URL/mention diganti token, sehingga komentar
  berbeda bisa kolaps. Split bisa gagal "tiap kelas butuh minimal 2 contoh".
- Dataset asli bukan UTF-8 murni (953 karakter rusak) dan 1.435 baris memuat
  escape `\xf0\x9f...`; `--encoding auto` + `repair_escaped_bytes` menangani.
  82 run escape tidak valid sengaja dibiarkan.
- Dedup masih **exact setelah normalisasi**; near-duplicate fuzzy belum ada.
- `pytest -q` menjadi `-qq` karena `addopts`; ringkasan hilang.
- Nama file aturan di root adalah `agents.md` (huruf kecil), bukan `AGENTS.md`.

## Dataset

`re_dataset.csv` = Ibrohim & Budi (2019), CC BY-NC-SA 4.0. Jangan commit,
jangan komersial, cantumkan sitasi. Detail: `docs/dataset.md`.

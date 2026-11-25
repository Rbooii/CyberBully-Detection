# Skills — CyberBully

Panduan operasional untuk agent. Aturan wajib tetap di `agents.md`; file ini
tidak menggantikannya dan tidak boleh dipakai untuk melonggarkan aturan.

## Environment (audit 2026-11-23)

- `ENV_TYPE=venv` (uv 0.13.8), `ENV_PATH=/Users/arcozkwn/.venvs/ml`
- `PYTHON=/Users/arcozkwn/.venvs/ml/bin/python` — Python 3.12.16, arm64
- Kernel Jupyter: "Python (ML Lab)" → `~/Library/Jupyter/kernels/ml/kernel.json`
- Tidak ada conda/pyenv. Jangan pakai Python Homebrew (3.15).
- Terpasang: torch 2.15.0 (MPS True), transformers 5.24.0, datasets 5.2.0,
  accelerate, scikit-learn 1.9.1, pandas 3.1.1, numpy 2.5.4,
  fastapi 0.165.0, pytest 9.2.0, nbformat 5.11.1, nbclient 0.11.0, httpx 0.28.1.

## Perintah

```bash
# install
uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"

# data (dataset proyek)
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.data \
    --input data/raw/re_dataset.csv --text-col Tweet \
    --label-col HS Abusive --positive 1 --label-mode any \
    --keep-cols HS Abusive

# baseline (F1 val 0,881)
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.baseline

# training smoke
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 128 --epochs 1 --batch-size 8 --max-length 32 --out models/smoke

# full training A (real-only)
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.train \
    --batch-size 16 --max-length 128 --class-weights \
    --out models/indobert_real

# augmentasi sintetis (hanya train)
/Users/arcozkwn/.venvs/ml/bin/python scripts/generate_synthetic.py
/Users/arcozkwn/.venvs/ml/bin/python scripts/check_synthetic.py
/Users/arcozkwn/.venvs/ml/bin/python scripts/augment_train.py
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.train \
    --train-file data/processed/train_augmented.csv --out models/indobert_aug

# evaluasi validation
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.evaluate --split val

# API + frontend
uvicorn api.main:app --reload
curl -s -X POST http://127.0.0.1:8000/compare \
  -H 'Content-Type: application/json' -d '{"text":"dasar bodoh"}'
cd interface && npm run dev

# test (addopts sudah -q; jangan tambah -q lagi)
/Users/arcozkwn/.venvs/ml/bin/python -m pytest

# reset artefak turunan (dry-run default)
/Users/arcozkwn/.venvs/ml/bin/python scripts/reset_generated.py
/Users/arcozkwn/.venvs/ml/bin/python scripts/reset_generated.py --yes
```

## Artefak saat ini (2026-11-25)

- `models/indobert_real` — model A (real-only) + `threshold.json` 0,42; ini yang
  dipakai API.
- `models/indobert_aug` — model B2, threshold `0.5`; mendeteksi lima kategori
  sulit, tetapi F1 agregat lebih rendah dari A.
- `out/model_a` dan `out/model_b` — metrik A/B2. Eval set 40 final: A F1 0,412;
  B2 F1 0,897. Test B2 tercatat pada threshold 0,05 sebelum policy diubah.
- `data/synthetic/synthetic_train.csv` — 20.000 baris (14k positif / 6k hard
  negative), termasuk pujian menyindir, sarkasme karya, gaslighting, subtweet,
  body shaming.
- `data/processed/train_augmented.csv` — 30.397 baris (10.397 real + 20k
  synthetic), sudah dipakai training B2.
- `data/eval/implicit_eval.csv` — 40 final + 10 usulan; gaslighting masih usulan.
  `evaluate.py` melewati baris `usulan`.
- Test A sudah dievaluasi pada 0,42; B2 tercatat pada 0,05. Threshold deploy B2
  sekarang 0,5; test pada 0,5 tidak dijalankan ulang.
- B2/A dapat dijalankan di API; `threshold.json` di folder model menentukan label.
- Eval set 50 masih usulan; per kategori belum terukur final.

## Colab

- Panduan end-to-end: `docs/guide.md`; detail Colab: `docs/colab.md`; full
  training A/B: `docs/colab_full_training.md`.
- `06` memakai `RUN_FULL = IN_COLAB`; di Colab otomatis training, di Mac skip.
- Untuk melanjutkan setelah disconnect: `RESUME = True`.
- Device otomatis CUDA > MPS > CPU; T4 memakai fp16 dan workers 2.
- Setelah selesai, unduh `models/indobert_real` dan `models/indobert_aug` ke
  laptop dan evaluasi lokal.

## Konvensi repo

- Frontend di `interface/` (Vite + React + TypeScript strict), bukan `frontend/`.
  Desain mengikuti `agent/design.md`, `agent/DESIGN_GUIDE.md`, dan
  `agent/globals.css` (Geist, monokrom, sidebar, light/dark).
- `agent/skills.md` dan `agent/memory.md` di-commit; perbarui `memory.md` di
  akhir sesi.
- Semua path lewat `cyberbully.config`; jangan hardcode path absolut.
- Setiap notebook wajib: Tujuan, Prasyarat, Estimasi waktu, Glosarium, Ringkasan;
  setiap sel kode didahului markdown ≥120 karakter. Ditegakkan
  `tests/test_notebooks.py`, termasuk larangan menyimpan output.

## Jebakan yang sudah terbukti

- **Training lokal dihentikan SIGTERM** di tengah epoch 2 (tanpa traceback/OOM).
  Jangan mengulang full training di shell agent; pakai Colab atau Terminal
  pemilik. Model final 3 epoch sudah diunduh dari Colab.
- **Sindiran lolos**: "Wah pintar sekali, sampai salah dua kali." diprediksi
  non-bully (p=0,048) bahkan oleh model final 3 epoch. Ini temuan kualitatif
  penting, bukan bug API.
- **transformers 5.24**, bukan 4.x: `processing_class`, `eval_strategy`, tanpa
  `warmup_ratio`/`save_safetensors`/`group_by_length`.
- `prajjwal1/bert-tiny` tokenizer gagal di transformers 5; pakai
  `hf-internal-testing/tiny-random-BertForSequenceClassification`.
- Dataset bukan UTF-8 murni (953 karakter rusak) dan 1.435 baris memuat escape
  `\xf0\x9f...`; `--encoding auto` + `repair_escaped_bytes` menangani.
- Dedup masih exact setelah normalisasi; near-duplicate fuzzy belum ada.
- `pytest -q` menjadi `-qq` karena `addopts`; ringkasan hilang.
- Nama file aturan di root adalah `agents.md` (huruf kecil), bukan `AGENTS.md`.

## Dataset

`re_dataset.csv` = Ibrohim & Budi (2019), CC BY-NC-SA 4.0. Jangan commit,
jangan komersial, cantumkan sitasi. Detail: `docs/dataset.md`.

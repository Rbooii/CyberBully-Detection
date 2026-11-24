# CyberBully Detection (Bahasa Indonesia)

Deteksi cyberbullying pada komentar berbahasa Indonesia dengan fine-tuning
IndoBERT. Task klasifikasi biner: `bully` (1) / `non-bully` (0), termasuk
tantangan sindiran tanpa kata kasar.

## Status

| Bagian | Status |
|---|---|
| Pipeline data | Selesai: encoding aman, repair emoji, label union, dedup sebelum split |
| Baseline TF-IDF + LogReg | Selesai, validation F1 bully **0,881** |
| IndoBERT | Model final 3 epoch, validation F1 **0,926**; test menunggu eval set final |
| API FastAPI | Selesai, diuji 200/422/503 dengan model final |
| Frontend `interface/` | Selesai, build & uji browser; API final diuji via curl |
| Notebook 00–06, 99 | Selesai dan lolos eksekusi lokal |
| Augmentasi sintetis | 15k siap (9k positif + 6k negatif), model B belum ditraining |
| Eval set manual | 20 contoh **usulan**, belum final (target ≥200) |
| Test set | **Belum dievaluasi**; menunggu eval set final dan threshold dibekukan |
| Laporan `99_report` | Template berisi hasil validation; menunggu test final |

Angka di atas adalah validation, bukan test. Model final 3 epoch sudah dilatih di
Colab T4 dan diunduh ke `models/indobert`; hasil test belum ada.

## Hasil validation

| Model | Threshold | Accuracy | Precision bully | Recall bully | F1 bully |
|---|---|---|---|---|---|
| TF-IDF + Logistic Regression | 0,40 | 0,865 | 0,860 | 0,903 | 0,881 |
| IndoBERT final 3 epoch | 0,50 | 0,918 | 0,934 | 0,918 | 0,926 |
| IndoBERT final (threshold tuned) | 0,42 | 0,922 | 0,933 | 0,925 | 0,929 |

Split yang sama, seed 42, validation 1.300 baris (723 positif). Selisih F1 0,003
antara threshold 0,5 dan 0,42 kecil; jangan mengklaim peningkatan berarti.

Catatan kualitatif: contoh sindiran "Wah pintar sekali, sampai salah dua kali."
masih diprediksi **non-bully** (p=0,048) oleh model final. Ini persis jenis
kesalahan yang menjadi fokus proyek; jangan menyimpulkan model sudah bagus hanya
dari F1 validation.

## Augmentasi data sintetis

Tersedia 15.000 contoh sintetis (9.000 positif, 6.000 hard negative) yang
**hanya boleh masuk train**. Generator dan validator ada di `scripts/`; CSV-nya
gitignored dan bisa dibuat ulang deterministik dengan seed 42.

```bash
python scripts/generate_synthetic.py
python scripts/check_synthetic.py
python scripts/augment_train.py

# train dengan data augmentasi
python -m cyberbully.train --train-file data/processed/train_augmented.csv \
    --batch-size 16 --max-length 128 --class-weights \
    --out models/indobert_aug
```

Rencana eksperimen: model A (real saja, F1 val 0,926) vs model B (real + 15k
sintetis) pada split/seed/hyperparameter sama. Model dipilih dari validation,
bukan eval set. Detail komposisi dan batasan ada di
[`data/synthetic/README.md`](data/synthetic/README.md).

## Mulai cepat (lokal)

```bash
# 1. environment
uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 2. data (lihat docs/dataset.md)
python -m cyberbully.data --input data/raw/re_dataset.csv \
    --text-col Tweet --label-col HS Abusive --positive 1 \
    --label-mode any --keep-cols HS Abusive

# 3. baseline
python -m cyberbully.baseline

# 4. smoke training
python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 --out models/smoke

# 5. training (lebih disarankan di Colab)
python -m cyberbully.train --batch-size 16 --max-length 128 --class-weights

# 6. evaluasi validation
python -m cyberbully.evaluate --split val

# 7. test sekali setelah threshold dari validation
python -m cyberbully.evaluate --split test --threshold <hasil-tuning> --confirm-test
```

Training penuh di Mac ini sempat berjalan satu epoch lalu dihentikan di tengah
epoch kedua (Mac tanpa fan). Panduan memindahkannya ke GPU T4:
[`docs/colab.md`](docs/colab.md).

## API dan frontend

```bash
# API (model dimuat sekali saat startup)
uvicorn api.main:app --reload

# frontend
cd interface && npm install && npm run dev
```

- `POST /predict` → `label`, `score`, `bully_probability`.
- `GET /health` → `status`, `model_loaded`.
- Model belum ada → **503**; input invalid → **422**.
- CORS hanya `http://localhost:5173` dan `http://127.0.0.1:5173`.

Detail frontend ada di [`interface/README.md`](interface/README.md).

## Dataset

`re_dataset.csv` — *Indonesian Abusive and Hate Speech Twitter Text*
([Kaggle](https://www.kaggle.com/datasets/ilhamfp31/indonesian-abusive-and-hate-speech-twitter-text),
repo asli [okkyibrohim](https://github.com/okkyibrohim/id-multi-label-hate-speech-and-abusive-language-detection)).
Lisensi **CC BY-NC-SA 4.0**: atribusi, non-komersial, share-alike.

Definisi label: `bully = HS == 1 or Abusive == 1` → 12.997 baris bersih,
7.224 positif. Skema, SHA-256, dan artefak encoding ada di
[`docs/dataset.md`](docs/dataset.md).

Sitasi:

> Muhammad Okky Ibrohim and Indra Budi. 2019. Multi-label Hate Speech and
> Abusive Language Detection in Indonesian Twitter. In *ALW3*, 46–57.

## Struktur

```
src/cyberbully/   config, preprocess, data, runtime, metrics, baseline,
                  synthetic, train, evaluate, predict
api/              FastAPI: /predict, /health
interface/        frontend Vite + React + TypeScript strict
docs/             dataset.md, colab.md
scripts/          generate_synthetic, check_synthetic, augment_train
notebooks/        00 setup, 01 EDA, 02 baseline, 03 error analysis,
                  04 comparison, 05 threshold, 06 Colab training, 99 report
data/raw/         dataset asli (gitignored)
data/processed/   train/val/test.csv + train_augmented.csv (gitignored)
data/synthetic/   data sintetis train (gitignored)
data/eval/        eval set manual + 20 usulan (di-commit)
agent/            skills.md + memory.md
models/           checkpoint (gitignored)
out/              metrik & artefak run (gitignored)
tests/            pytest
```

## Aturan ML yang dipegang

- Dedup dan normalisasi **sebelum** split; tidak ada teks yang muncul di train
  dan test.
- Hyperparameter dan threshold dipilih dari validation.
- Test set dievaluasi sekali; `--confirm-test` adalah pengaman.
- Preprocessing minimal: stopword, tanda baca, dan emoji dipertahankan.
- Accuracy bukan metrik utama; precision, recall, F1 bully, dan confusion matrix
  wajib dilaporkan.
- Baris eval set berstatus `usulan` dilewati sampai direview pemilik.

## Keterbatasan & etika

Model ini alat bantu moderasi, bukan penghukum otomatis. Konteks percakapan,
bias dataset, sindiran yang lolos, dan kata kasar akrab dapat menghasilkan false
negative maupun false positive. Dataset non-komersial; demo untuk riset/edukasi
dan tidak boleh dipakai untuk keputusan otomatis terhadap individu.

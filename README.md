# CyberBully Detection (Bahasa Indonesia)

Deteksi cyberbullying pada komentar berbahasa Indonesia dengan fine-tuning
IndoBERT. Task klasifikasi biner: `bully` (1) / `non-bully` (0), termasuk
tantangan sindiran tanpa kata kasar.

## Status

| Bagian | Status |
|---|---|
| Pipeline data | Selesai: encoding aman, repair emoji, label union, dedup sebelum split |
| Baseline TF-IDF + LogReg | Selesai, validation F1 bully **0,881** |
| IndoBERT | Checkpoint epoch 1 (preliminary), validation F1 **0,914**; 3 epoch menunggu Colab |
| API FastAPI | Selesai, diuji 200/422/503 |
| Frontend `interface/` | Selesai, build & uji browser dengan checkpoint epoch 1 |
| Notebook 00–06, 99 | Selesai dan lolos eksekusi lokal |
| Eval set manual | 20 contoh **usulan**, belum final (target ≥200) |
| Test set | **Belum dievaluasi**; menunggu model final + threshold validation |
| Laporan `99_report` | Template berisi hasil validation; menunggu test final |

Angka di atas adalah validation, bukan test. Model IndoBERT yang dipakai demo
masih 1 epoch; hasilnya belum boleh disebut performa final.

## Hasil validation (sementara)

| Model | Threshold | Accuracy | Precision bully | Recall bully | F1 bully |
|---|---|---|---|---|---|
| TF-IDF + Logistic Regression | 0,40 | 0,865 | 0,860 | 0,903 | 0,881 |
| IndoBERT, epoch 1 | 0,50 | 0,907 | 0,939 | 0,891 | 0,914 |
| IndoBERT, epoch 1 (threshold tuned) | 0,34 | 0,905 | 0,918 | 0,911 | 0,915 |

Split yang sama, seed 42, validation 1.300 baris (723 positif). Perbedaan 0,001
F1 antara threshold 0,5 dan 0,34 tidak bisa disebut peningkatan berarti.

Catatan kualitatif: contoh sindiran "Wah pintar sekali, sampai salah dua kali."
masih diprediksi **non-bully** oleh checkpoint epoch 1. Ini persis jenis
kesalahan yang menjadi fokus proyek; jangan menyimpulkan model sudah bagus hanya
dari F1 validation.

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

# demo dengan checkpoint epoch 1
CYBERBULLY_MODEL_DIR=models/indobert/checkpoints/checkpoint-650 \
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
                  train, evaluate, predict
api/              FastAPI: /predict, /health
interface/        frontend Vite + React + TypeScript strict
docs/             dataset.md, colab.md
notebooks/        00 setup, 01 EDA, 02 baseline, 03 error analysis,
                  04 comparison, 05 threshold, 06 Colab training, 99 report
data/raw/         dataset asli (gitignored)
data/processed/   train/val/test.csv (gitignored)
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

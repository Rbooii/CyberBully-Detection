# CyberBully Detection (Bahasa Indonesia)

Deteksi cyberbullying pada teks bahasa Indonesia dengan fine-tuning IndoBERT.
Task klasifikasi biner: `bully` (1) / `non-bully` (0), termasuk tantangan
sindiran tanpa kata kasar.

## Status

- [x] Pipeline data: loading aman, repair emoji, label union, dedup, split 80/10/10
- [x] Inti training/evaluasi/prediksi (MPS dan CUDA)
- [x] Notebook setup + EDA + training Colab
- [ ] Baseline TF-IDF + Logistic Regression
- [ ] Fine-tuning IndoBERT penuh
- [ ] Eval set manual, error analysis, API/frontend, laporan

Belum ada angka performa yang boleh dilaporkan. Smoke test memakai model acak
kecil; F1-nya tidak bermakna.

## Environment

Venv `ml-lab` (uv, Python 3.12):

```bash
uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"
export PYTORCH_ENABLE_MPS_FALLBACK=1   # wajib di Mac
```

Di Colab (GPU T4) tidak perlu fallback MPS. Panduan lengkap:
[`docs/colab.md`](docs/colab.md).

## Dataset

`re_dataset.csv` — *Indonesian Abusive and Hate Speech Twitter Text*
([Kaggle](https://www.kaggle.com/datasets/ilhamfp31/indonesian-abusive-and-hate-speech-twitter-text),
repo asli [okkyibrohim](https://github.com/okkyibrohim/id-multi-label-hate-speech-and-abusive-language-detection)).
Lisensi **CC BY-NC-SA 4.0**: atribusi, non-komersial, share-alike.

`bully = HS == 1 or Abusive == 1` → 12.997 baris bersih, 7.224 positif.
Detail skema, SHA-256, dan artefak encoding ada di
[`docs/dataset.md`](docs/dataset.md).

Sitasi:

> Muhammad Okky Ibrohim and Indra Budi. 2019. Multi-label Hate Speech and
> Abusive Language Detection in Indonesian Twitter. In *ALW3*, 46–57.

## Mulai cepat (lokal)

```bash
# 1. data
python -m cyberbully.data --input data/raw/re_dataset.csv \
    --text-col Tweet --label-col HS Abusive --positive 1 \
    --label-mode any --keep-cols HS Abusive

# 2. smoke test (wajib sebelum run penuh)
python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 --out models/smoke

# 3. training IndoBERT
python -m cyberbully.train --batch-size 16 --max-length 128 --class-weights

# 4. evaluasi validation
python -m cyberbully.evaluate --split val

# 5. test (sekali, setelah threshold dari validation)
python -m cyberbully.evaluate --split test --threshold 0.5 --confirm-test

# test suite
pytest
```

Artefak training (`run_meta.json`, `val_metrics.json`, `val_predictions.csv`,
checkpoint) tersimpan di folder `--out`. `run_meta.json` mencatat versi paket,
device, seed, dan git commit agar run bisa direproduksi.

## Notebook

| Notebook | Isi |
|---|---|
| [`00_colab_setup`](notebooks/00_colab_setup.ipynb) | Colab, paket, Drive, split data |
| [`01_eda`](notebooks/01_eda.ipynb) | label, panjang teks, duplikat, keseimbangan |
| [`06_colab_training`](notebooks/06_colab_training.ipynb) | smoke, full training, evaluasi val |

Semua notebook berbahasa Indonesia dan menjelaskan setiap sel kode untuk pembaca
yang baru belajar ML/NLP. Struktur ini ditegakkan oleh `tests/test_notebooks.py`.

## Struktur

```
src/cyberbully/   logika reusable (config, preprocess, data, runtime, metrics,
                  train, evaluate, predict)
api/              FastAPI (belum dibuat)
interface/        frontend Vite + React + TS (belum dibuat)
docs/             dataset.md, colab.md
notebooks/        eksplorasi & laporan
agent/            skills.md + memory.md untuk sesi agent berikutnya
data/raw/         dataset asli (gitignored)
data/processed/   train/val/test.csv (gitignored)
data/eval/        eval set manual (di-commit)
```

## Aturan ML yang dipegang

- Dedup dan normalisasi **sebelum** split; tidak boleh ada teks yang muncul di
  train dan test.
- Hyperparameter dan threshold dipilih dari validation.
- Test set dievaluasi sekali; `--confirm-test` adalah pengaman.
- Preprocessing minimal: stopword, tanda baca, dan emoji dipertahankan.
- Accuracy bukan metrik utama; precision, recall, F1 bully, dan confusion matrix
  wajib dilaporkan.

## Keterbatasan & etika

Model ini alat bantu moderasi, bukan penghukum otomatis. Konteks percakapan,
bias dataset, sindiran yang lolos, dan kata kasar akrab dapat menghasilkan false
negative maupun false positive. Dataset berlisensi non-komersial; demo ini untuk
riset/edukasi dan tidak boleh dipakai untuk keputusan otomatis terhadap individu.

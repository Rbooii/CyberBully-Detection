# CyberBully Detection (Bahasa Indonesia)

Deteksi cyberbullying pada komentar berbahasa Indonesia dengan fine-tuning
IndoBERT. Task klasifikasi biner: `bully` (1) / `non-bully` (0), termasuk
tantangan sindiran tanpa kata kasar.

**Panduan lengkap dari nol:** [`docs/guide.md`](docs/guide.md).
**Full training Colab A/B:** [`docs/colab_full_training.md`](docs/colab_full_training.md).

## Status

| Bagian | Status |
|---|---|
| Pipeline data | Selesai: encoding aman, repair emoji, label union, dedup sebelum split |
| Baseline TF-IDF + LogReg | Selesai; referensi validation F1 bully **0,881** |
| IndoBERT | A: val F1 **0,926** (threshold 0,42). B2: val F1 **0,917** (threshold 0,5) |
| API FastAPI | Selesai; dua model tersedia, `/compare`, threshold per model |
| Frontend `interface/` | Selesai; `npm install` sebelum `npm run dev` |
| Notebook 00–06, 99 | Selesai; butuh data/model untuk dijalankan |
| Augmentasi sintetis | 20k bertarget sudah dibuat; `train_augmented` 30.397 baris siap |
| Eval set manual | 40 `final`, 10 `usulan` (target ≥200) |
| Test set | A: F1 **0,925** (threshold 0,42). B2: tercatat 0,919 pada 0,05; threshold deploy 0,5 belum di-test ulang |
| Laporan `99_report` | Template berisi hasil referensi; B2 belum masuk laporan |

B2 dilatih dengan 20k sintetis bertarget. Pada uji manual lima kategori sulit,
B2 memberi p≈1,0 untuk semuanya; A masih 0,002–0,11. Namun F1 validation B2
lebih rendah dari A. Test B2 pernah dijalankan pada threshold 0,05; setelah
policy threshold diperbaiki, threshold deploy menjadi 0,5 dan test tidak diulang
agar tidak menjadi evaluasi kedua. Ini keterbatasan yang harus ditulis.

## Hasil validation (referensi run sebelumnya)

| Model | Threshold | Accuracy | Precision bully | Recall bully | F1 bully |
|---|---|---|---|---|---|
| TF-IDF + Logistic Regression | 0,40 | 0,865 | 0,860 | 0,903 | 0,881 |
| IndoBERT A — real-only | 0,50 | 0,918 | 0,934 | 0,918 | 0,926 |
| IndoBERT A — threshold tuned | 0,42 | 0,922 | 0,933 | 0,925 | 0,929 |
| IndoBERT B2 — asli + 20k sintetis | 0,50 | 0,908 | 0,922 | 0,913 | 0,917 |

Split yang sama, seed 42, validation 1.300 baris (723 positif). Selisih F1 0,003
antara threshold 0,5 dan 0,42 kecil; jangan mengklaim peningkatan berarti.

Catatan kualitatif: B2 mendeteksi kelima contoh sulit (subtweet, backhanded,
sarkasme karya, gaslighting, body shaming) dengan p≈1,0, sedangkan A gagal.
Tetapi B2 juga lebih rendah pada F1 validation/test agregat. Ini trade-off yang
harus dilaporkan, bukan disembunyikan.

## Eval set manual (40 baris final)

| Model | Threshold | Accuracy | Precision bully | Recall bully | F1 bully |
|---|---:|---:|---:|---:|---:|
| IndoBERT A — real-only | 0,42 | 0,500 | 1,000 | 0,259 | 0,412 |
| IndoBERT B2 — asli + sintetis | 0,50 | 0,850 | 0,839 | 0,963 | 0,897 |

B2 unggul pada pujian menyindir, body shaming, sarkasme karya, dan subtweet
(akurasi 1,0), tetapi lebih banyak false positive pada kritik dan netral.
Gaslighting belum masuk hitungan karena 5 barisnya masih `usulan`. Sepuluh baris
usulan lain juga belum dihitung; jangan menyebut ini angka final seluruh eval set.

## Augmentasi data sintetis

Tersedia 20.000 contoh sintetis (14.000 positif, 6.000 hard negative) yang
**hanya boleh masuk train**. Versi baru mencakup pujian menyindir, sarkasme
karya, gaslighting, subtweet, dan body shaming, dengan hard negative berupa
pujian/permintaan maaf tulus. Generator dan validator ada di `scripts/`; CSV-nya
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

Rencana eksperimen: model A (real saja, F1 val 0,926) vs model B (real + 20k
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

# 5. training model A (real-only; lebih disarankan di Colab)
python -m cyberbully.train --batch-size 16 --max-length 128 --class-weights \
    --out models/indobert_real

# 6. evaluasi validation A
python -m cyberbully.evaluate --model-dir models/indobert_real \
    --split val --out-dir out/model_a

# 7. test A sekali setelah threshold dari validation
python -m cyberbully.evaluate --model-dir models/indobert_real --split test \
    --threshold <hasil-tuning> --out-dir out/model_a --confirm-test
```

Model B dilatih dengan `--train-file data/processed/train_augmented.csv` dan
`--out models/indobert_aug`. Panduan lengkap dua model di GPU T4:
[`docs/colab_full_training.md`](docs/colab_full_training.md).

## API dan frontend

```bash
# API (model dimuat sekali saat startup)
uvicorn api.main:app --reload

# frontend
cd interface && npm install && npm run dev
```

- `POST /compare` → hasil Model A dan B sekaligus, termasuk `threshold` masing-masing.
- `POST /predict?model=a` atau `?model=b` → hasil satu model.
- `GET /health` → `status`, `model_loaded`, `models`, dan `thresholds` per A/B.
- Model A default `models/indobert_real`; B `models/indobert_aug`.
- Model belum lengkap → **503**; input invalid → **422**.
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
docs/             guide.md, colab_full_training.md, dataset.md, colab.md
scripts/          generate/check/augment synthetic, reset_generated
notebooks/        00 setup, 01 EDA, 02 baseline, 03 error analysis,
                  04 comparison, 05 threshold, 06 Colab training, 99 report
data/raw/         dataset asli (gitignored)
data/processed/   train/val/test.csv + train_augmented.csv (gitignored)
data/synthetic/   data sintetis train (gitignored)
data/eval/        eval set manual + 50 usulan (di-commit)
agent/            skills.md, memory.md, referensi desain
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

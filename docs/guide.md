# Panduan Lengkap dari Nol

Panduan ini menuntun dari repo kosong sampai model, API, frontend, dan laporan
bisa dijalankan. Laporan siap dibaca ada di
`docs/laporan_pipeline_cyberbullying.docx`; sumbernya `docs/laporan_pipeline.md`
dan dibangun ulang dengan `python scripts/build_report.py`. Ditulis untuk pembaca
yang baru belajar ML/NLP: setiap perintah
dijelaskan tujuannya, output yang diharapkan, dan cara menangani kegagalan umum.

Model dan artefak turunan **sengaja dihapus** dari repo lokal. Semua langkah di
bawah bisa diulang dari `data/raw/re_dataset.csv` yang tetap disimpan.

Dokumen pendukung:

- [`docs/dataset.md`](dataset.md) — sumber, lisensi, skema, SHA-256.
- [`docs/colab_full_training.md`](colab_full_training.md) — full training A/B di Colab.
- [`docs/colab.md`](colab.md) — detail training Colab, resume, troubleshooting.
- `README.md` — ringkasan project dan status.

## 0. Apa yang akan dibangun

```
data/raw/re_dataset.csv
        │
        ├── pipeline data ──► data/processed/{train,val,test}.csv
        │                           │
        │                           ├── baseline TF-IDF
        │                           └── IndoBERT (MPS/Colab)
        │                                     │
        │                                     ├── models/indobert_real
        │                                     └── metrik validation
        │
        ├── generator sintetis ──► data/synthetic/synthetic_train.csv
        │                                     │
        │                                     └── train augmented
        │
        └── eval set manual ──► data/eval/implicit_eval.csv

model ──► API FastAPI ──► frontend React
   │
   └── evaluasi validation → threshold → test sekali → laporan
```

Aturan utama:

- Dedup dan normalisasi **sebelum** split.
- Validation untuk memilih hyperparameter dan threshold.
- Test hanya dievaluasi **sekali**, setelah model dan threshold dibekukan.
- Data sintetis hanya untuk train; tidak pernah untuk validation/test.
- Jangan commit data mentah, data proses, model, atau `node_modules`.

## 1. Prasyarat

- MacBook Apple Silicon (arm64) untuk training lokal, atau akun Google untuk Colab.
- Python ≥ 3.10 di environment `ml-lab`
  (`/Users/arcozkwn/.venvs/ml` pada mesin ini).
- Node.js ≥ 18 dan npm untuk frontend.
- Git dan akses ke repo
  `https://github.com/Rbooii/CyberBully-Detection`.
- File `re_dataset.csv` (lihat bagian 3).
- Waktu: setup 10–15 menit; training Colab 5–60 menit tergantung antrean GPU.

Cek cepat:

```bash
python --version
node --version
npm --version
python -c "import torch; print(torch.backends.mps.is_available())"
```

Di Mac, hasil terakhir harus `True`.

## 2. Clone dan environment

```bash
git clone https://github.com/Rbooii/CyberBully-Detection.git
cd CyberBully-Detection

uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

Kalau memakai shell tanpa aktivasi:

```bash
/Users/arcozkwn/.venvs/ml/bin/python -c "import cyberbully, torch; print(cyberbully.__version__, torch.__version__)"
```

Jangan memakai Python sistem/Homebrew dan jangan membuat environment baru tanpa
izin. `-e` berarti *editable*: perubahan kode langsung terbaca.

## 3. Dataset

Dataset: **Indonesian Abusive and Hate Speech Twitter Text**.

- Kaggle: <https://www.kaggle.com/datasets/ilhamfp31/indonesian-abusive-and-hate-speech-twitter-text>
- Sumber asli: <https://github.com/okkyibrohim/id-multi-label-hate-speech-and-abusive-language-detection>
- Lisensi: **CC BY-NC-SA 4.0** (atribusi, non-komersial, share-alike).
- Sitasi: Ibrohim & Budi (2019), *Multi-label Hate Speech and Abusive Language
  Detection in Indonesian Twitter*, ALW3.
- File: `re_dataset.csv`, 13.169 baris, 1.858.473 byte.
- SHA-256: `44c04e31ad4b7ee4a95f1884e7af4da2c44b69762143eb2de0ede7f90502735e`.

Letakkan file di `data/raw/re_dataset.csv`. Folder ini gitignored; jangan commit
dataset. Jangan scraping platform dan jangan mengunduh dataset lain tanpa izin.

Fakta kualitas data yang perlu diketahui:

- Bukan UTF-8 murni; ada 953 karakter rusak.
- 1.435 baris menyimpan emoji sebagai escape `\xf0\x9f...`.
- Kolom `HS` dan `Abusive` adalah label biner 0/1.
- Penulis asli sudah mengganti username/URL menjadi token `USER`/`URL`.

## 4. Struktur repo

```
src/cyberbully/   logika reusable
api/              FastAPI
interface/        Vite + React + TypeScript strict
docs/             guide, dataset, colab
notebooks/        00–06, 99
scripts/          generate/check/augment synthetic, reset artifacts
tests/            pytest
data/raw/         dataset asli (gitignored)
data/processed/   split (gitignored)
data/synthetic/   data sintetis (gitignored)
data/eval/        eval set manual (di-commit)
models/           model (gitignored)
out/              metrik/artefak (gitignored)
```

## 5. Pipeline data

```bash
python -m cyberbully.data \
    --input data/raw/re_dataset.csv \
    --text-col Tweet \
    --label-col HS Abusive \
    --positive 1 \
    --label-mode any \
    --keep-cols HS Abusive
```

Yang dilakukan:

1. Membaca CSV dengan encoding aman; byte rusak diganti dan diberi peringatan.
2. Memperbaiki emoji yang ter-escape menjadi karakter asli.
3. Menggabungkan `HS` atau `Abusive` menjadi label `bully`.
4. Normalisasi ringan: casefold, URL/mention disamarkan, emoji/tanda baca tetap.
5. Dedup setelah normalisasi, **sebelum** split.
6. Split stratifikasi 80/10/10 dengan seed 42.

Output yang diharapkan:

```
dataset bersih: 12997 baris
  train 10397 baris  label={0: 4618, 1: 5779}
  val    1300 baris  label={0: 577, 1: 723}
  test   1300 baris  label={0: 578, 1: 722}
```

Peringatan `953 karakter bukan UTF-8 valid` normal. Kalau jumlah baris jauh
berbeda, periksa file masukan dan nama kolom.

Verifikasi:

```bash
head -2 data/processed/train.csv
python - <<'PY'
import pandas as pd
for name in ("train", "val", "test"):
    df = pd.read_csv(f"data/processed/{name}.csv")
    print(name, len(df), df["label"].value_counts().to_dict())
PY
```

## 6. Baseline TF-IDF

Baseline wajib sebelum menyimpulkan IndoBERT.

```bash
python -m cyberbully.baseline
```

Output: `models/baseline_tfidf.joblib`, `out/baseline_val.json`,
`out/baseline_top_features.json`, `out/baseline_val_predictions.csv`.

Referensi hasil (bukan jaminan): threshold 0,40; accuracy 0,865; precision bully
0,860; recall 0,903; **F1 bully 0,881**.

## 7. Smoke training

Tujuan: memastikan data, tokenizer, Trainer, dan penyimpanan bekerja. Model kecil
dan acak; metriknya **tidak bermakna**.

```bash
python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 \
    --out models/smoke
```

Di Mac harus terlihat `device: mps`. Selesai dalam beberapa menit dan menghasilkan
`models/smoke/run_meta.json`.

## 8. Full training A/B

Panduan detail khusus Colab: [`docs/colab_full_training.md`](colab_full_training.md).

Dua model yang dibandingkan:

| Model | Data train | Output |
|---|---|---|
| A | 10.397 komentar asli | `models/indobert_real` |
| B | 10.397 asli + 20.000 sintetis | `models/indobert_aug` |

### Opsi A — Colab T4 (disarankan)

1. Upload `re_dataset.csv` ke `MyDrive/cyberbully/data/`.
2. Buka Colab → **Runtime → T4 GPU**.
3. Jalankan `notebooks/00_colab_setup.ipynb` sampai split selesai.
4. Train A (real-only):

```bash
python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --epochs 3 --batch-size 16 --max-length 128 --class-weights \
    --out /content/drive/MyDrive/cyberbully/models/indobert_real
```

5. Generate/check/augment sintetis (bagian 9), lalu train B:

```bash
python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --train-file data/processed/train_augmented.csv \
    --epochs 3 --batch-size 16 --max-length 128 --class-weights \
    --out /content/drive/MyDrive/cyberbully/models/indobert_aug
```

6. Unduh file root kedua folder ke laptop.

Referensi A: 1.950 langkah, sekitar 3–4 menit di T4. Kalau OOM:
`--batch-size 8 --grad-accum 2 --max-length 96`. Kalau runtime mati:
tambahkan `--resume`.

### Opsi B — lokal MPS

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
caffeinate -i python -m cyberbully.train \
    --epochs 3 --batch-size 16 --max-length 128 \
    --class-weights --out models/indobert_real
```

Untuk B, tambahkan `--train-file data/processed/train_augmented.csv` dan
`--out models/indobert_aug`. Mac ini tanpa fan: pakai charger dan ventilasi.
Training lokal pernah menerima SIGTERM di tengah epoch 2 tanpa traceback; kalau
itu terjadi, gunakan Colab.

Output penting di folder `--out`:

```
config.json
model.safetensors
tokenizer.json
tokenizer_config.json
run_meta.json
val_metrics.json
val_predictions.csv
checkpoints/
```

Referensi A: accuracy 0,918; precision 0,934; recall 0,918; **F1 bully 0,926**
pada threshold 0,5. B2: val F1 0,917 pada threshold 0,5; lebih baik pada kasus
sulit tetapi lebih rendah secara agregat.

## 9. Augmentasi sintetis (opsional)

Synthetic **hanya untuk train**. Validation/test tetap data asli. Data baru
mencakup pujian menyindir, sarkasme karya, gaslighting, subtweet, dan body
shaming, dengan hard negative pujian/permintaan maaf tulus.

```bash
python scripts/generate_synthetic.py
python scripts/check_synthetic.py
python scripts/augment_train.py
```

Output yang diharapkan:

```
dataset sintetis: 20000 baris
train augmented: 30397 baris (10397 real + 20000 synthetic)
```

`check_synthetic.py` harus melaporkan nol duplikat/PII/overlap. Kalau gagal,
jangan training. Train model B ke folder terpisah:

```bash
python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --train-file data/processed/train_augmented.csv \
    --epochs 3 --batch-size 16 --max-length 128 \
    --class-weights --out models/indobert_aug
```

Bandingkan model A (real-only) dan B di validation. Pilih dari validation, bukan
eval set/test. Kalau F1 turun, jangan pakai B. Data sintetis dibuat dari
template + 35 seed tulis tangan; bisa overfit pola dan lebih pendek dari tweet
asli.

## 10. Evaluasi

### Validation A/B

```bash
python -m cyberbully.evaluate \
    --model-dir models/indobert_real --split val --out-dir out/model_a

python -m cyberbully.evaluate \
    --model-dir models/indobert_aug --split val --out-dir out/model_b
```

Output: `out/model_a/val_metrics.json`, `out/model_b/val_metrics.json`, dan
prediksi validation masing-masing.

### Threshold dari validation

Buka `notebooks/05_threshold_tuning.ipynb`. Notebook memilih threshold terpisah
dan menulis:

```
out/model_a/threshold.json
out/model_b/threshold.json
```

Referensi A: threshold 0,42; F1 0,929; recall 0,925; precision 0,933. B2:
threshold 0,5; F1 0,917; lebih baik di kasus sulit, lebih rendah agregat.

### Test sekali per model

```bash
python -m cyberbully.evaluate \
    --model-dir models/indobert_real --split test \
    --threshold <threshold_A> --out-dir out/model_a --confirm-test

python -m cyberbully.evaluate \
    --model-dir models/indobert_aug --split test \
    --threshold <threshold_B> --out-dir out/model_b --confirm-test
```

`--confirm-test` adalah pengaman; file `out/model_a/test_metrics.json` dan
`out/model_b/test_metrics.json` menolak run kedua tanpa `--allow-rerun-test`.
Jangan memakai test untuk memilih model/threshold.

### Eval set manual

`data/eval/implicit_eval.csv` berisi kolom `text,label,category,status`. Baris
dengan `status=usulan` dilewati sampai Anda review. Target ≥200 baris `final`.
Jangan mengisi eval set dengan prediksi model.

```bash
python -m cyberbully.evaluate \
    --model-dir models/indobert_real --split val \
    --implicit-eval data/eval/implicit_eval.csv --out-dir out/model_a

python -m cyberbully.evaluate \
    --model-dir models/indobert_aug --split val \
    --implicit-eval data/eval/implicit_eval.csv --out-dir out/model_b
```

Hasil per kategori: `out/model_a/implicit_metrics.json` dan
`out/model_b/implicit_metrics.json`.

## 11. API

```bash
uvicorn api.main:app --reload
```

Default: model A di `models/indobert_real`, model B di `models/indobert_aug`.
Bisa diarahkan:

```bash
CYBERBULLY_MODEL_A=models/indobert_real \
CYBERBULLY_MODEL_B=models/indobert_aug \
    uvicorn api.main:app --reload
```

Cek:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/compare \
  -H 'Content-Type: application/json' \
  -d '{"text":"Dasar bodoh, kerjaan kayak gini aja nggak becus."}'

# satu model
curl -s -X POST http://127.0.0.1:8000/predict?model=b \
  -H 'Content-Type: application/json' -d '{"text":"dasar bodoh"}'

# input kosong harus 422
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' -d '{"text":"   "}'
```

`/health` melaporkan model dan threshold yang aktif. `/compare` mengembalikan
`threshold` tiap model. Tanpa model lengkap: `/compare` → **503**; input invalid
→ **422**. CORS hanya `localhost:5173` dan
`127.0.0.1:5173`.

## 12. Frontend

```bash
cd interface
npm install
npm run dev
```

Buka <http://localhost:5173>. Halaman menampilkan dua panel: Model A (data asli)
dan Model B (asli + sintetis), dengan tombol **Bandingkan teks**. API default
`http://localhost:8000`; ubah lewat `interface/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

Verifikasi build:

```bash
npm run typecheck
npm run build
npm run lint
```

State loading/error ditangani; jangan menampilkan stack trace ke pengguna.

## 13. Notebook

| Notebook | Kapan dijalankan | Isi |
|---|---|---|
| `00_colab_setup` | Colab | runtime, clone, install, Drive, split |
| `01_eda` | setelah split | label, panjang, duplikat, keseimbangan |
| `02_baseline_tfidf` | setelah split | baseline, metrik, top fitur |
| `03_error_analysis` | setelah prediksi val | FN/FP, subgroup |
| `04_model_comparison` | setelah baseline + IndoBERT | perbandingan validation |
| `05_threshold_tuning` | setelah val_predictions | PR curve, threshold |
| `06_colab_training` | Colab | smoke + full training + eval val |
| `99_report` | akhir | laporan dari artefak, bukan training |

Semua notebook wajib punya Tujuan, Prasyarat, Estimasi waktu, Glosarium, dan
Ringkasan; setiap sel kode didahului penjelasan. Ditegakkan
`tests/test_notebooks.py`.

## 14. Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `ModuleNotFoundError: cyberbully` | Paket belum di-install di runtime | `%pip install -e ".[dev]"`, atau `pip install -e .` |
| `CUDA: False` di Colab | Runtime bukan GPU | Runtime → Change runtime type → T4 GPU |
| MPS `False` | Mesin/env salah | Pakai `ml-lab`, cek `torch.backends.mps.is_available()` |
| Proses MPS mati tanpa traceback | SIGTERM/batas eksternal | Jangan ulang di shell agent; pakai Colab |
| `CUDA out of memory` | Batch/seq terlalu besar | `--batch-size 8 --grad-accum 2 --max-length 96` |
| `No such file: data/processed/train.csv` | Split belum dibuat | Jalankan pipeline data |
| `953 karakter bukan UTF-8` | Artefak file asli | Normal; pipeline sudah menangani |
| `test set hanya boleh...` | `--confirm-test` belum ada | Tambahkan hanya untuk evaluasi final |
| API 503 | Model tidak ada/gagal dimuat | Latih model, cek `CYBERBULLY_MODEL_A`/`B`, lihat `/health` |
| CORS error | Origin bukan dev | Jalankan frontend di port 5173 |
| `npm` gagal | `node_modules` hilang | `cd interface && npm install` |
| `check_synthetic.py` gagal | Duplikat/PII/overlap | Perbaiki generator/data sebelum training |

## 15. Reset artefak

Untuk mengulang dari nol tanpa menyentuh kode, raw data, dan eval set:

```bash
python scripts/reset_generated.py        # dry-run
python scripts/reset_generated.py --yes  # hapus
```

Yang dihapus: isi `models/`, `out/`, `data/processed/`, CSV
`data/synthetic/`, `interface/node_modules`, `interface/dist`. Yang
dipertahankan: `data/raw/`, `data/eval/`, kode, `.gitkeep`, dan
`data/synthetic/README.md`. Setelah reset, API akan 503 sampai model dilatih
ulang.

## 16. Checklist dari nol

- [ ] Clone repo dan install `.[api,dev]`.
- [ ] `PYTORCH_ENABLE_MPS_FALLBACK=1` dan MPS `True`.
- [ ] `data/raw/re_dataset.csv` ada; lisensi dicatat.
- [ ] Pipeline data menghasilkan 12.997 baris dan split 10.397/1.300/1.300.
- [ ] Baseline dijalankan.
- [ ] Smoke training lolos (metrik diabaikan).
- [ ] Full training A (real-only) selesai di `models/indobert_real`.
- [ ] Synthetic 20k lolos check; train augmented dibuat.
- [ ] Full training B (asli+sintetis) selesai di `models/indobert_aug`.
- [ ] Validation A dan B dievaluasi.
- [ ] Threshold A dan B dipilih dari validation masing-masing.
- [ ] Eval set manual direview (≥200 `final`).
- [ ] Test A dan B masing-masing dievaluasi sekali dengan `--confirm-test`.
- [ ] API `/health`, `/predict`, `/compare`, 422/503 diuji.
- [ ] Frontend build dan dev diuji (dua panel A/B).
- [ ] Notebook 99 diisi dari artefak A/B.
- [ ] `pytest` hijau; tidak ada data/model di staging git.

## 17. Angka referensi

Angka dari run sebelumnya, **bukan jaminan**; hardware/versi bisa mengubah hasil.

| Model | Threshold | Accuracy | Precision bully | Recall bully | F1 bully |
|---|---|---|---|---|---|
| Baseline TF-IDF | 0,40 | 0,865 | 0,860 | 0,903 | 0,881 |
| IndoBERT A — real-only | 0,50 | 0,918 | 0,934 | 0,918 | 0,926 |
| IndoBERT A — threshold tuned | 0,42 | 0,922 | 0,933 | 0,925 | 0,929 |
| IndoBERT B2 — asli + 20k sintetis | 0,50 | 0,908 | 0,922 | 0,913 | 0,917 |

Test set belum dievaluasi pada run referensi. Eval set manual masih 50 usulan;
hasil eksplorasi 70% pada contoh sulit **bukan** hasil final.

Temuan penting: sindiran "Wah pintar sekali, sampai salah dua kali." masih
diprediksi non-bully (p≈0,048) oleh model final. Ini alasan proyek tidak boleh
hanya melaporkan F1 validation.

## 18. Lisensi dan etika

Dataset CC BY-NC-SA 4.0: wajib atribusi, non-komersial, share-alike. Model adalah
alat bantu moderasi, bukan penghukum otomatis. Konteks percakapan, sindiran
halus, bias anotasi, dan kata kasar akrab bisa menghasilkan false positive/
negative. Jangan memakai satu skor untuk menjatuhkan sanksi tanpa peninjauan
manusia.

## 19. Aturan reproducibility

- Seed 42 untuk split dan training.
- Jangan mengubah split/hyperparameter saat membandingkan model.
- Simpan `run_meta.json`; catat versi Python, torch, transformers, dan git commit.
- Jangan memilih threshold/model dari test atau eval set.
- Data sintetis hanya train; jangan mencampur ke eval/test.
- Jika hasil berubah, laporkan penyebabnya (versi, hardware, data, seed).

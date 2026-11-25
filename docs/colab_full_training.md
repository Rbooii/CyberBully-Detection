# Full Training di Colab — Dua Model A/B

Panduan ini khusus untuk **melatih penuh dua model** dari nol di Colab GPU T4:

| Model | Data train | Output |
|---|---|---|
| **A** | 10.397 komentar asli | `models/indobert_real` |
| **B** | 10.397 asli + 20.000 sintetis | `models/indobert_aug` |

Keduanya memakai validation/test asli yang sama, seed 42, dan hyperparameter
yang sama. Perbedaan hasil hanya berasal dari augmentasi data train.

Panduan umum: [`guide.md`](guide.md). Detail Colab lain: [`colab.md`](colab.md).
Repo: <https://github.com/Rbooii/CyberBully-Detection>.

## 0. Sebelum mulai

Siapkan:

- Akun Google dan akses Colab.
- File `re_dataset.csv` di laptop.
- Repo GitHub (public) sudah berisi kode terbaru.
- Waktu: 10–15 menit setup, 5–15 menit per model di T4.
- Dataset berlisensi CC BY-NC-SA 4.0; jangan commit/upload ke repo publik.

Struktur Drive yang dipakai:

```
MyDrive/cyberbully/
├── data/re_dataset.csv
├── models/
│   ├── indobert_real/
│   └── indobert_aug/
└── runs/
```

## 1. Aktifkan GPU dan ambil kode

1. Buka <https://colab.research.google.com>.
2. **Runtime → Change runtime type → T4 GPU → Save**.
3. Cek:

```python
import torch
print(torch.__version__, torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
```

`CUDA: True` wajib.

Clone repo:

```bash
!git clone https://github.com/Rbooii/CyberBully-Detection.git /content/CyberBully
%cd /content/CyberBully
!pip install -q -e ".[dev]"
```

Kalau folder sudah ada:

```bash
%cd /content/CyberBully
!git pull origin main
!pip install -q -e ".[dev]"
```

Verifikasi:

```python
import cyberbully, transformers
print(cyberbully.__version__, transformers.__version__)
```

`ModuleNotFoundError: cyberbully` berarti install gagal/sel install belum
dijalankan. Ulangi `%pip install -e ".[dev]"` dari `/content/CyberBully`.

## 2. Mount Drive dan taruh dataset

```python
from google.colab import drive
drive.mount("/content/drive")
```

Upload `re_dataset.csv` ke `MyDrive/cyberbully/data/`, lalu:

```bash
!mkdir -p /content/CyberBully/data/raw
!cp /content/drive/MyDrive/cyberbully/data/re_dataset.csv \
    /content/CyberBully/data/raw/re_dataset.csv
```

Jangan letakkan dataset di repo publik. Data mentah tetap di Drive sebagai
sumber permanen.

## 3. Buat split data

```bash
!python -m cyberbully.data \
    --input data/raw/re_dataset.csv \
    --text-col Tweet \
    --label-col HS Abusive \
    --positive 1 \
    --label-mode any \
    --keep-cols HS Abusive
```

Output yang diharapkan:

```
dataset bersih: 12997 baris
  train 10397 baris  label={0: 4618, 1: 5779}
  val    1300 baris  label={0: 577, 1: 723}
  test   1300 baris  label={0: 578, 1: 722}
```

Peringatan 953 karakter bukan UTF-8 valid berasal dari file asli. Kalau jumlah
baris jauh berbeda, berhenti dan periksa CSV/kolom.

## 4. Smoke test (wajib, sekali)

```bash
!python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 \
    --out models/smoke
```

Model acak; F1 tidak bermakna. Tujuannya memastikan data, tokenizer, Trainer,
dan penyimpanan bekerja. Lanjut hanya jika exit code 0.

## 5. Full training Model A — real-only

```bash
!python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --epochs 3 --batch-size 16 --max-length 128 \
    --class-weights \
    --out /content/drive/MyDrive/cyberbully/models/indobert_real
```

Yang diharapkan:

- 1.950 langkah (3 × 650).
- T4 sekitar 3–5 menit untuk dataset ini.
- Setiap epoch menyimpan checkpoint ke Drive.
- Akhir training: model, tokenizer, `run_meta.json`, `val_metrics.json`,
  `val_predictions.csv` di folder output.

Referensi validation A: F1 bully **0,926** pada threshold 0,5 (hardware/versi
bisa mengubah sedikit).

Kalau OOM:

```bash
--batch-size 8 --grad-accum 2 --max-length 96
```

Kalau runtime mati, salin perintah yang sama dan tambahkan `--resume`.

## 6. Siapkan data sintetis untuk Model B

```bash
!python scripts/generate_synthetic.py
!python scripts/check_synthetic.py
!python scripts/augment_train.py
```

Output yang diharapkan:

```
dataset sintetis: 20000 baris
train augmented: 30397 baris (10397 real + 20000 synthetic)
```

Data baru mencakup 14.000 positif: sindiran inti, merendahkan, satir, pujian
menyindir (backhanded), sarkasme karya, gaslighting, subtweet, dan body shaming.
Hard negative 6.000: kritik membangun, pujian tulus, permintaan maaf tulus,
netral, becanda akrab, dan perhatian tulus.

`check_synthetic.py` harus melaporkan:

- 0 duplikat
- 0 PII/URL/akun
- 0 overlap dengan train/val/test/eval

Kalau gagal, jangan training. Data sintetis hanya untuk train; validation/test
tetap data asli.

## 7. Full training Model B2 — real + sintetis bertarget

```bash
!python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --train-file data/processed/train_augmented.csv \
    --epochs 3 --batch-size 16 --max-length 128 \
    --class-weights \
    --out /content/drive/MyDrive/cyberbully/models/indobert_aug
```

Catatan:

- `--train-file` mengganti train saja; validation tetap
  `data/processed/val.csv`.
- Jangan arahkan `--out` ke `indobert_real`; model A akan tertimpa.
- Waktu lebih lama dari A karena train 30.397 baris.
- B2 dilatih dengan data sintetis 20k; bandingkan per kategori, bukan hanya F1 agregat.

Jika memakai notebook `06_colab_training.ipynb`:

1. Jalankan `00_colab_setup` sampai split.
2. Di sel runtime notebook 06, untuk A: `RUN_AUGMENTED = False`.
3. Setelah A selesai, ubah `RUN_AUGMENTED = True`, jalankan ulang sel 1
   (runtime) dan sel full training. Output otomatis ke `indobert_aug`.

## 8. Unduh kedua model ke laptop

Dari Drive, unduh **file root** setiap folder:

```
indobert_real/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
├── run_meta.json
├── val_metrics.json
└── val_predictions.csv

indobert_aug/
└── (file yang sama)
```

Folder `checkpoints/` tidak perlu diunduh; biarkan di Drive sebagai backup.
Letakkan di repo lokal:

```
models/indobert_real/
models/indobert_aug/
```

Jangan commit folder model (gitignored).

## 9. Evaluasi validation dan threshold

Di laptop, dari root repo:

```bash
cd ~/Documents/CODINGAN/Machine-learning/CyberBully
export PYTORCH_ENABLE_MPS_FALLBACK=1

python -m cyberbully.evaluate \
    --model-dir models/indobert_real --split val --out-dir out/model_a

python -m cyberbully.evaluate \
    --model-dir models/indobert_aug --split val --out-dir out/model_b
```

Lalu buka `notebooks/05_threshold_tuning.ipynb`. Notebook memilih threshold
terpisah dan menulis:

```
out/model_a/threshold.json
out/model_b/threshold.json
models/indobert_real/threshold.json
models/indobert_aug/threshold.json
```

Dua file terakhir dibaca API saat startup, sehingga label `/predict` dan
`/compare` memakai threshold beku, bukan 0,5 default. Kalau F1 terbaik mentok
di batas grid atau hanya menang <0,002 dari 0,5, notebook memakai 0,5.

Bandingkan F1, precision, recall, dan confusion matrix di
`notebooks/04_model_comparison.ipynb`. Pilih model untuk klaim utama dari
**validation**, bukan eval set/test.

## 10. Evaluasi test sekali per model

Setelah threshold masing-masing dibekukan:

```bash
python -m cyberbully.evaluate \
    --model-dir models/indobert_real --split test \
    --threshold <threshold_A> --out-dir out/model_a --confirm-test

python -m cyberbully.evaluate \
    --model-dir models/indobert_aug --split test \
    --threshold <threshold_B> --out-dir out/model_b --confirm-test
```

Masing-masing hanya sekali. File hasil:

```
out/model_a/test_metrics.json
out/model_b/test_metrics.json
```

Jangan mengulang test untuk mencari angka yang lebih bagus.

## 11. Eval set manual

`data/eval/implicit_eval.csv` berisi 50 usulan. Review dan ubah `status`
menjadi `final` sampai ≥200 baris. Baris `usulan` dilewati otomatis.

```bash
python -m cyberbully.evaluate \
    --model-dir models/indobert_real --split val \
    --implicit-eval data/eval/implicit_eval.csv --out-dir out/model_a

python -m cyberbully.evaluate \
    --model-dir models/indobert_aug --split val \
    --implicit-eval data/eval/implicit_eval.csv --out-dir out/model_b
```

Hasil per kategori ada di `out/model_a/implicit_metrics.json` dan
`out/model_b/implicit_metrics.json`. Eval set untuk laporan, bukan memilih model.

## 12. API dan frontend perbandingan

```bash
uvicorn api.main:app --reload
```

Default model A `models/indobert_real`, model B `models/indobert_aug`. Bisa
diubah:

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
  -d '{"text":"Wah pintar sekali, sampai salah dua kali."}'
```

Frontend:

```bash
cd interface
npm install
npm run dev
```

Buka <http://localhost:5173>, masukkan teks, klik **Bandingkan teks**. Dua panel
A/B akan tampil. Jika salah satu model belum ada, API `/compare` mengembalikan
503 dan frontend menampilkan pesan.

## 13. Resume dan troubleshooting

| Gejala | Solusi |
|---|---|
| `CUDA: False` | Runtime → T4 GPU, restart |
| OOM | `--batch-size 8 --grad-accum 2 --max-length 96` |
| Runtime mati | Ulangi setup + data, lalu training dengan `--resume` |
| `ModuleNotFoundError` | `%pip install -e ".[dev]"` dari repo |
| `check_synthetic.py` gagal | Jangan training; perbaiki duplikat/PII/overlap |
| Model B menimpa A | Pastikan `--out` ke folder berbeda |
| API 503 | Salah satu/kedua folder model tidak ada; cek `/health` |
| Frontend error koneksi | API belum jalan atau `VITE_API_URL` salah |
| Drive lambat | Data di `/content`, checkpoint saja di Drive |

Checkpoint ada di `<out>/checkpoints/`. Untuk melanjutkan:

```bash
python -m cyberbully.train ... --out <out-yang-sama> --resume
```

## 14. Checklist

- [ ] GPU T4 aktif dan `CUDA: True`.
- [ ] Dataset ada di Drive dan `/content/CyberBully/data/raw`.
- [ ] Split 10.397/1.300/1.300.
- [ ] Smoke test lolos.
- [ ] Model A selesai di `indobert_real`.
- [ ] Synthetic 20k lolos check.
- [ ] Model B selesai di `indobert_aug`.
- [ ] Kedua model diunduh ke laptop.
- [ ] Validation A/B dievaluasi.
- [ ] Threshold A/B disimpan terpisah.
- [ ] Test A/B masing-masing sekali.
- [ ] Eval set manual direview.
- [ ] API `/compare` dan frontend diuji.
- [ ] Laporan `99_report` diisi.

## 15. Angka referensi

| Model | Threshold | Accuracy | Precision bully | Recall bully | F1 bully |
|---|---|---|---|---|---|
| A real-only (referensi) | 0,50 | 0,918 | 0,934 | 0,918 | 0,926 |
| A tuned (referensi) | 0,42 | 0,922 | 0,933 | 0,925 | 0,929 |
| B2 real+20k sintetis | 0,50 | 0,908 | 0,922 | 0,913 | 0,917 |

Angka referensi berasal dari run sebelumnya, bukan jaminan. Bandingkan A dan B
pada run Anda sendiri dengan split/seed yang sama. Jika B lebih rendah, laporkan
apa adanya; augmentasi sintetis bukan jaminan peningkatan.

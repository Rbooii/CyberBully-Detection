# Menjalankan Training di Google Colab

Panduan ini untuk Colab **GPU gratis (T4)**, tanpa mengubah aturan repo:
logika training tetap di `src/cyberbully/`, notebook hanya memanggil CLI.

> Konflik aturan: `agents.md` §8 semula melarang training dari notebook.
> Pengecualian di sini hanya untuk Colab, dan tetap dengan syarat notebook
> memanggil `python -m cyberbully.train`, bukan menyalin kode training.

## Ringkasan alur

```
GitHub / zip  →  /content/CyberBully      (kode, sekali per sesi)
Google Drive  →  MyDrive/cyberbully/      (dataset & checkpoint, permanen)
/data/processed  →  train/val/test.csv    (dibuat ulang tiap sesi)
models/indobert  →  checkpoint ke Drive   (agar tidak hilang saat disconnect)
```

## 1. Siapkan runtime

1. Buka <https://colab.research.google.com>.
2. **Runtime → Change runtime type → T4 GPU → Save**.
3. Cek di sel pertama:

```python
import torch
print(torch.__version__)
print("CUDA:", torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
```

`CUDA: True` wajib. Kalau `False`, runtime belum GPU — ulangi langkah 2.

## 2. Ambil kode

### Opsi A — clone dari GitHub (disarankan)

Repo belum punya remote saat panduan ini ditulis. Setelah Anda push sendiri:

```bash
git remote add origin https://github.com/<username>/cyberbully.git
git push -u origin main
```

Di Colab:

```python
REPO_URL = "https://github.com/<username>/cyberbully.git"
```

Repo publik cukup; data dan model tetap tidak masuk git.

### Opsi B — zip/Drive

Zip folder proyek (tanpa `data/`, `models/`, `node_modules/`), unggah ke Drive,
lalu:

```python
!unzip -q /content/drive/MyDrive/cyberbully/cyberbully.zip -d /content
```

Sesuaikan `PROJECT_DIR` bila nama folder berbeda.

## 3. Install

```python
%cd /content/CyberBully
!pip install -q -e ".[dev]"
```

- `-e` (editable) membuat perubahan kode langsung terbaca.
- Colab sudah punya `torch`; `torch>=2.2` terpenuhi sehingga tidak diunduh ulang.
- `transformers`, `datasets`, `accelerate`, dan `fastapi` akan diunduh sekali
  per sesi. Ini normal (1–3 menit).

## 4. Mount Drive dan taruh dataset

```python
from google.colab import drive
drive.mount("/content/drive")
```

Layout yang disarankan:

```
MyDrive/cyberbully/
├── data/re_dataset.csv
├── models/
└── runs/
```

Salin dataset ke repo supaya I/O training cepat (Drive lambat untuk baca acak):

```bash
mkdir -p /content/CyberBully/data/raw
cp /content/drive/MyDrive/cyberbully/data/re_dataset.csv \
   /content/CyberBully/data/raw/re_dataset.csv
```

Jangan commit dataset (lisensi CC BY-NC-SA 4.0, lihat `docs/dataset.md`).

## 5. Siapkan split

```bash
python -m cyberbully.data \
    --input data/raw/re_dataset.csv \
    --text-col Tweet \
    --label-col HS Abusive \
    --positive 1 \
    --label-mode any \
    --keep-cols HS Abusive
```

Output yang diharapkan: 12.997 baris; train 10.397, val 1.300, test 1.300.
Peringatan `953 karakter bukan UTF-8 valid` memang berasal dari file asli.

## 6. Smoke test dulu (wajib)

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1   # tidak berpengaruh di Colab, aman
python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 \
    --out models/smoke
```

Tujuannya hanya memastikan pipeline jalan. Model ini **acak dan kecil**; F1-nya
tidak bermakna dan tidak boleh dilaporkan.

## 7. Full training

```bash
python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --epochs 3 --batch-size 16 --max-length 128 \
    --class-weights \
    --out /content/drive/MyDrive/cyberbully/models/indobert
```

Perkiraan di T4: 30–60 menit untuk 3 epoch. Angka ini perkiraan, bukan janji.
Jika OOM:

```bash
--batch-size 8 --grad-accum 2 --max-length 96
```

Checkpoint disimpan ke Drive setiap epoch. Kalau runtime mati, ulangi setup lalu:

```bash
python -m cyberbully.train ... --resume
```

Latih ulang dari checkpoint terakhir, bukan dari nol.

## 8. Evaluasi validation

```bash
python -m cyberbully.evaluate \
    --model-dir /content/drive/MyDrive/cyberbully/models/indobert \
    --split val \
    --out-dir /content/drive/MyDrive/cyberbully/runs/val
```

Threshold final dipilih dari validation (notebook `05_threshold_tuning` nanti).
**Test set belum boleh disentuh** sampai laporan akhir per model.

Saat sudah final:

```bash
python -m cyberbully.evaluate --split test \
    --threshold <hasil tuning val> \
    --confirm-test \
    --model-dir ... --out-dir ...
```

`--confirm-test` adalah pengaman; test set hanya dievaluasi sekali.

## 9. Bedakan MPS (Mac) vs CUDA (Colab)

| Hal | Mac MPS | Colab T4 |
|---|---|---|
| `fp16` | **tidak boleh** | otomatis aktif |
| `dataloader_num_workers` | 0 | 2 |
| `PYTORCH_ENABLE_MPS_FALLBACK` | wajib | tidak perlu |
| Checkpoint | `models/` lokal | Drive |
| Waktu | lebih lambat | lebih cepat |

Kode memilih device otomatis (`auto`); tidak perlu mengubah argumen.

## 10. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `CUDA: False` | Runtime bukan GPU; ubah runtime type lalu restart. |
| `CUDA out of memory` | Kecilkan `--batch-size`, naikkan `--grad-accum`, turunkan `--max-length`. |
| Runtime disconnect | Colab gratis membatasi idle/waktu. Pakai `--out` ke Drive + `--resume`. |
| Training sangat lambat | Dataset dibaca dari Drive; salin ke `/content`, tulis checkpoint saja ke Drive. |
| `401/403` dari HuggingFace | Model publik; biasanya rate limit. Tunggu atau set `HF_TOKEN` di Colab Secrets. |
| `No such file: data/processed/train.csv` | Belum menjalankan langkah 5. |
| `ModuleNotFoundError: cyberbully` | `pip install -e .` belum dijalankan atau `%cd` salah. |
| Versi `transformers` berubah | Colab dan lokal bisa beda. Catat versi di `run_meta.json`. |

## 11. Checklist sebelum menutup tab

- [ ] `run_meta.json` dan `val_metrics.json` ada di Drive.
- [ ] Checkpoint terakhir ada di `models/indobert/checkpoints/`.
- [ ] Tidak ada test set yang dievaluasi tanpa `--confirm-test`.
- [ ] Catatan waktu per epoch disalin ke `agent/memory.md`.
- [ ] Dataset tidak diunggah ke repo publik.

## 12. Etika

Model ini alat bantu moderasi, bukan penghukum otomatis. Dataset berlisensi
**CC BY-NC-SA 4.0**: cantumkan sitasi Ibrohim & Budi (2019), jangan pakai
komersial, dan jangan bagikan ulang data tanpa lisensi yang sama.

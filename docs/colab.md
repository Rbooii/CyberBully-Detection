# Training di Google Colab (GPU T4)

Panduan ini menjelaskan cara melatih IndoBERT untuk proyek ini dari nol di
Colab, menyimpan checkpoint ke Google Drive, dan memindahkan hasilnya kembali ke
laptop. Repo: <https://github.com/Rbooii/CyberBully-Detection>.

Colab dipakai karena MacBook Air M3 ini tanpa fan. Training lokal lewat MPS
sempat berjalan satu epoch (F1 validation 0,914) lalu proses dihentikan di tengah
epoch kedua. Checkpoint epoch 1 tetap tersimpan di
`models/indobert/checkpoints/checkpoint-650` dan boleh dipakai untuk demo
sementara, bukan untuk laporan final.

## Alur singkat

```
GitHub  ──clone──►  /content/CyberBully       (kode, hilang saat runtime mati)
Drive   ──copy───►  data/raw/re_dataset.csv   (dataset, permanen)
data    ──split──►  data/processed/*.csv      (dibuat ulang tiap sesi)
train   ──save───►  MyDrive/cyberbully/models/indobert  (checkpoint, permanen)
```

## 0. Yang perlu disiapkan

- Akun Google dan akses Colab.
- Repo GitHub sudah berisi kode terbaru (public, aman karena data/model
  gitignored).
- File `re_dataset.csv` ada di laptop.
- Waktu: 10–15 menit setup + 30–60 menit training di T4.
- Tidak perlu kartu kredit untuk GPU gratis; kuota Colab bisa berubah.

## 1. Buka Colab dan aktifkan GPU

1. Buka <https://colab.research.google.com>.
2. **Runtime → Change runtime type → T4 GPU → Save**.
3. Di sel pertama:

```python
import torch
print("torch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
```

`CUDA: True` wajib. Kalau `False`, ulangi langkah 2 dan restart runtime.

## 2. Ambil kode

Di Colab:

```bash
!git clone https://github.com/Rbooii/CyberBully-Detection.git /content/CyberBully
%cd /content/CyberBully
```

Kalau folder sudah ada (runtime baru, Drive belum di-mount):

```bash
%cd /content/CyberBully
!git pull origin main
```

Repo publik, jadi tidak perlu token. Jangan pernah menaruh token di sel notebook
yang output-nya tersimpan.

Alternatif tanpa GitHub: zip folder proyek (tanpa `data/`, `models/`,
`node_modules/`), unggah ke Drive, lalu `unzip` ke `/content/CyberBully`.

## 3. Install paket

```bash
!pip install -q -e ".[dev]"
```

- `-e` = editable, perubahan kode langsung terbaca.
- Colab sudah punya `torch`; `torch>=2.2` terpenuhi sehingga tidak diunduh ulang.
- `transformers`, `accelerate`, `datasets`, dan `fastapi` diunduh sekali per
  sesi (1–3 menit).
- Jika muncul konflik dependensi, restart runtime lalu ulangi install.

Cek instalasi:

```python
import cyberbully, transformers
print(cyberbully.__version__, transformers.__version__)
```

## 4. Mount Drive dan siapkan dataset

```python
from google.colab import drive
drive.mount("/content/drive")
```

Layout yang dipakai:

```
MyDrive/cyberbully/
├── data/re_dataset.csv
├── models/
└── runs/
```

Upload `re_dataset.csv` ke `MyDrive/cyberbully/data/` lewat panel Files Drive.
Jangan upload ke repo publik: lisensinya CC BY-NC-SA 4.0 dan aturan repo melarang
commit data.

Salin ke runtime supaya pembacaan cepat:

```bash
!mkdir -p /content/CyberBully/data/raw
!cp /content/drive/MyDrive/cyberbully/data/re_dataset.csv \
    /content/CyberBully/data/raw/re_dataset.csv
```

## 5. Buat split

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

Peringatan `953 karakter bukan UTF-8 valid` berasal dari file asli; pipeline
sudah menanganinya. Kalau angkanya jauh berbeda, berhenti dan periksa CSV.

## 6. Smoke test

Tujuannya hanya memastikan data, tokenizer, Trainer, dan penyimpanan bekerja.
Model yang dipakai kecil dan acak, jadi **F1-nya tidak bermakna**.

```bash
!python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 \
    --out models/smoke
```

Harus selesai dalam beberapa menit dan menghasilkan `models/smoke/run_meta.json`.

## 7. Full training

Cara termudah: buka `notebooks/06_colab_training.ipynb`, jalankan semua sel.
Notebook menetapkan `RUN_FULL = IN_COLAB`, sehingga di Colab training otomatis
jalan dan di Mac otomatis dilewati. Alternatif CLI:

```bash
!python -m cyberbully.train \
    --model indobenchmark/indobert-base-p1 \
    --epochs 3 --batch-size 16 --max-length 128 \
    --class-weights \
    --out /content/drive/MyDrive/cyberbully/models/indobert
```

Perkiraan T4: 30–60 menit untuk 3 epoch. Angka ini perkiraan, bukan jaminan.

Yang dipantau tiap epoch:

- `eval_f1_bully` — metrik pemilih checkpoint terbaik.
- `eval_precision_bully` dan `eval_recall_bully` — arah error.
- loss training tidak boleh turun sementara F1 validation stagnan (overfitting).

Checkpoint disimpan setiap epoch ke Drive. Jika GPU kehabisan memori:

```bash
--batch-size 8 --grad-accum 2 --max-length 96
```

atau turunkan `--max-length 64`.

## 8. Melanjutkan setelah runtime mati

Colab gratis bisa memutus koneksi. Setelah runtime baru:

1. Ulangi langkah 1–5 (GPU, clone, install, Drive, data).
2. Buka `06_colab_training.ipynb`.
3. Ubah `RESUME = True`.
4. Jalankan sel full training.

`--resume` mengambil checkpoint terakhir di
`MyDrive/cyberbully/models/indobert/checkpoints/`. Untuk mengulang dari nol,
hapus folder model di Drive terlebih dahulu.

## 9. Unduh hasil ke laptop

Yang perlu diunduh dari Drive:

```
models/indobert/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
├── run_meta.json
├── val_metrics.json
└── val_predictions.csv
```

Letakkan di `models/indobert/` pada repo lokal (folder ini gitignored). Setelah
itu evaluasi dijalankan di laptop, bukan di Colab:

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 1. validation saja
python -m cyberbully.evaluate --split val

# 2. tuning threshold dari validation
#    (buka notebooks/05_threshold_tuning.ipynb)

# 3. test SEKALI dengan threshold hasil tuning
python -m cyberbully.evaluate --split test \
    --threshold <angka dari out/threshold.json> \
    --confirm-test
```

Jangan menjalankan test sebelum model dan threshold dibekukan. `--confirm-test`
adalah pengaman; `out/test_metrics.json` yang sudah ada akan menolak run kedua
tanpa `--allow-rerun-test`.

## 10. Setelah model ada

```bash
# API
uvicorn api.main:app --reload

# Frontend
cd interface
npm install
npm run dev
```

API memuat model sekali saat startup. Kalau `models/indobert` belum ada,
`GET /health` mengembalikan `model_loaded: false` dan `POST /predict`
mengembalikan **503**, bukan crash.

Untuk demo memakai checkpoint epoch 1 lokal:

```bash
CYBERBULLY_MODEL_DIR=models/indobert/checkpoints/checkpoint-650 \
    uvicorn api.main:app --reload
```

Tandai hasil demo sebagai **preliminary**; checkpoint itu baru 1 epoch.

## 11. MPS (Mac) vs CUDA (Colab)

| Hal | Mac MPS | Colab T4 |
|---|---|---|
| `fp16` | tidak boleh | otomatis aktif |
| `dataloader_num_workers` | 0 | 2 |
| `PYTORCH_ENABLE_MPS_FALLBACK` | wajib | tidak perlu |
| Checkpoint | `models/` lokal | Drive |
| Panas | laptop hangat | tidak memanaskan laptop |
| Waktu | lebih lambat | lebih cepat |

Kode memilih device otomatis (`cuda` > `mps` > `cpu`); tidak perlu mengubah
argumen device.

## 12. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `CUDA: False` | Runtime bukan GPU. Runtime → Change runtime type → T4 GPU, restart. |
| `CUDA out of memory` | Kecilkan `--batch-size`, naikkan `--grad-accum`, turunkan `--max-length`. |
| Runtime disconnect | Colab gratis membatasi idle/waktu. Checkpoint ke Drive + `RESUME = True`. |
| Training terasa lambat | Data dibaca dari Drive. Salin dataset ke `/content`; tulis checkpoint saja ke Drive. |
| `401/403` HuggingFace | Model publik; biasanya rate limit. Tunggu atau set `HF_TOKEN` di Colab Secrets. |
| `No such file: data/processed/train.csv` | Langkah split belum dijalankan. |
| `ModuleNotFoundError: cyberbully` | `pip install -e .` belum jalan atau `%cd` salah. |
| `RUN_FULL` tidak jalan | Di luar Colab nilainya `False`. Buka di Colab, atau ubah manual. |
| `--resume` tidak menemukan checkpoint | Path `--out` berbeda dari run sebelumnya, atau folder Drive terhapus. |
| Versi `transformers` beda | Catat versi di `run_meta.json`; jangan mencampur artefak dari run berbeda tanpa catatan. |
| Model tidak terbaca di API | Pastikan folder berisi `config.json`, bobot, dan tokenizer; cek `GET /health`. |

## 13. Checklist sebelum menutup tab

- [ ] `run_meta.json`, `val_metrics.json`, dan `val_predictions.csv` ada di Drive.
- [ ] Checkpoint terakhir ada di `models/indobert/checkpoints/`.
- [ ] Tidak ada test set yang dievaluasi tanpa `--confirm-test`.
- [ ] Waktu per epoch dan versi `transformers` dicatat di `agent/memory.md`.
- [ ] Dataset dan model tidak diunggah ke repo publik.
- [ ] Hasil akhir diunduh ke laptop sebelum runtime dihapus.

## 14. Lisensi dan etika

Dataset berlisensi **CC BY-NC-SA 4.0**: wajib atribusi (Ibrohim & Budi, 2019),
non-komersial, dan share-alike untuk data olahan yang dibagikan. Model ini alat
bantu moderasi, bukan penghukum otomatis. Konteks percakapan, sindiran halus, dan
kata kasar akrab tetap bisa salah dibaca.

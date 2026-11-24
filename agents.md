# AGENTS.md

Instruksi tetap untuk AI coding agent yang bekerja di repo ini. Baca seluruhnya sebelum mengubah apa pun. Kalau instruksi di chat bertentangan dengan file ini, ikuti chat, lalu sebutkan konfliknya.

Bahasa komunikasi dengan pemilik repo: **Indonesia**. Identifier kode, nama file, dan commit message: **English**. Komentar kode: singkat, boleh Indonesia.

---

## 1. Ringkasan project

Deteksi cyberbullying pada teks bahasa Indonesia (komentar media sosial) dengan fine-tuning IndoBERT.

- Task: klasifikasi biner `bully` (1) / `non-bully` (0).
- Tantangan utama: **sindiran/satire tanpa kata kasar**. Model yang hanya belajar "ada kata kasar = bully" dianggap gagal, sekalipun metrik di test set tinggi.
- Base model: `indobenchmark/indobert-base-p1`. Pembanding: `indolem/indobertweet-base-uncased`.
- Output akhir: model, API (FastAPI), frontend demo (React), notebook laporan.
- Pemilik repo adalah mahasiswa CS yang masih belajar workflow ML dan notebook. Jelaskan *kenapa* di balik keputusan teknis penting, jangan hanya memberi kode.

## 2. Environment

- Mesin: MacBook Air M3 (Apple Silicon, arm64, tanpa fan). Training memakai backend **MPS**.
- Environment Python: **`ml-lab`**. Jenisnya (conda / venv / pyenv-virtualenv) dan path-nya harus dideteksi, jangan ditebak.
  - Hasil audit (2026-11-23, disetujui pemilik): `ENV_TYPE=venv (uv 0.13.8)`, `ENV_PATH=/Users/arcozkwn/.venvs/ml`, `PYTHON=/Users/arcozkwn/.venvs/ml/bin/python`
  - Terpasang: Python 3.12.16, torch 2.15.0 (MPS True), transformers 5.24.0, scikit-learn 1.9.1, pandas 3.1.1, fastapi 0.165.0, pytest 9.2.0.
- Semua perintah Python dijalankan **di dalam `ml-lab`**. Jangan memakai Python sistem/global. Jangan membuat environment baru tanpa izin.
- Wajib: `export PYTORCH_ENABLE_MPS_FALLBACK=1` saat training/inference di Mac.
- Versi minimum: Python ≥ 3.10, `transformers` ≥ 4.46, Node ≥ 18 (frontend).
- Verifikasi MPS: `python -c "import torch; print(torch.backends.mps.is_available())"` harus `True`.
- Colab (opsional): GPU T4 memakai CUDA. Di sana `fp16` otomatis aktif dan `num_workers=2`; panduan ada di `docs/colab.md` dan `docs/colab_full_training.md`.

## 3. Struktur repo

```
.
├── agents.md
├── README.md
├── pyproject.toml
├── agent/              # skills.md (cara kerja) + memory.md (log keputusan), di-commit
├── docs/               # guide.md, colab_full_training.md, dataset.md, colab.md
├── data/
│   ├── raw/            # dataset asli, read-only, gitignored
│   ├── processed/      # train/val/test.csv, gitignored
│   ├── synthetic/      # data sintetis untuk train, gitignored
│   └── eval/           # test set manual (implicit_eval.csv), di-commit
├── notebooks/          # eksplorasi & laporan, bernomor
├── src/cyberbully/     # semua logika reusable
│   ├── config.py       # path, nama model, konstanta
│   ├── preprocess.py   # normalize_text + repair escape
│   ├── data.py         # load, encoding, map label, dedup, split
│   ├── runtime.py      # device auto (CUDA/MPS/CPU), seed, workers
│   ├── metrics.py      # metrik biner + threshold dari validation
│   ├── baseline.py     # TF-IDF + Logistic Regression (pembanding)
│   ├── synthetic.py    # generator/validator data sintetis untuk train
│   ├── train.py        # fine-tuning (HF Trainer)
│   ├── evaluate.py     # metrik val/test + eval set manual
│   └── predict.py      # Predictor (dipakai API & notebook)
├── scripts/            # utilitas CLI: generate/check/augment synthetic, reset artifacts
├── api/                # FastAPI: /predict, /compare, /health
├── interface/          # Vite + React + TypeScript (frontend)
├── models/             # checkpoint hasil training, gitignored
├── out/                # metrik & artefak run, gitignored
└── tests/              # pytest
```

Aturan penempatan:
- Logika yang dipakai lebih dari satu tempat **harus** ada di `src/cyberbully/`, bukan di notebook atau API.
- `api/` dan notebook hanya *memanggil* `src/`.
- Script sekali pakai ke `scripts/`, bukan `src/`.

## 4. Perintah standar

```bash
# setup (sekali)
pip install -e ".[api,dev]"

# data (contoh dataset proyek; lihat docs/dataset.md)
python -m cyberbully.data --input data/raw/re_dataset.csv \
    --text-col Tweet --label-col HS Abusive --positive 1 --label-mode any \
    --keep-cols HS Abusive

# baseline pembanding
python -m cyberbully.baseline

# augmentasi sintetis (hanya train)
python scripts/generate_synthetic.py
python scripts/check_synthetic.py
python scripts/augment_train.py
python -m cyberbully.train --train-file data/processed/train_augmented.csv \
    --out models/indobert_aug

# training: smoke dulu, baru penuh
python -m cyberbully.train \
    --model hf-internal-testing/tiny-random-BertForSequenceClassification \
    --subset 256 --epochs 1 --batch-size 16 --max-length 64 --out models/smoke
python -m cyberbully.train --batch-size 16 --class-weights --out models/indobert_real
# kalau OOM: --batch-size 8 --grad-accum 2 --max-length 64
# model lain: --model indolem/indobertweet-base-uncased --out models/indobertweet

# evaluasi (test hanya dengan --confirm-test dan threshold dari validation)
python -m cyberbully.evaluate --split val

# reset artefak (dry-run default)
python scripts/reset_generated.py
python scripts/reset_generated.py --yes

# test
pytest -q

# API
uvicorn api.main:app --reload

# frontend
cd interface && npm install && npm run dev
```

Training penuh tidak dijalankan dari notebook lokal. Pengecualian: notebook Colab
boleh **memanggil** `python -m cyberbully.train` (lihat `docs/colab.md` dan
`notebooks/06_colab_training.ipynb`), tetapi logika training tetap di `src/`.

## 5. Aturan Python

- Type hint untuk fungsi publik. Docstring satu baris yang menjelaskan *tujuan*, bukan mengulang nama fungsi.
- Gaya: PEP 8, `snake_case` untuk fungsi/variabel, `PascalCase` untuk kelas. Path memakai `pathlib`, bukan string concatenation.
- Path proyek selalu lewat `cyberbully.config`, jangan hardcode path absolut.
- Tidak ada `print` debug yang tersisa di `src/` selain log yang disengaja.
- Jangan menelan exception diam-diam (`except: pass`). Tangani yang spesifik atau biarkan naik.
- Dependency baru: tambahkan ke `pyproject.toml` dan sebutkan alasannya. Jangan meng-install paket yang tidak dipakai.
- Setiap perubahan di `preprocess.py` / `data.py` wajib disertai atau memperbarui test di `tests/`.

## 6. Aturan ML (penting, jangan dilanggar)

1. **Tidak boleh ada data leakage.** Dedup dan normalisasi dilakukan *sebelum* split. Teks yang sama atau nyaris sama tidak boleh muncul di train dan test. Fit apa pun (TF-IDF, scaler, threshold) hanya pada data train/val.
2. **Test set disentuh sekali** untuk laporan akhir per model. Pilihan hyperparameter dan threshold diambil dari **validation set**.
3. **Seed tetap** (`config.SEED = 42`) untuk split dan training supaya hasil bisa direproduksi.
4. **Jangan hanya melaporkan accuracy.** Wajib: precision, recall, F1 untuk kelas bully, confusion matrix, dan akurasi per kategori di `data/eval/implicit_eval.csv`.
5. **Bandingkan dengan baseline** TF-IDF + Logistic Regression. Kalau IndoBERT tidak jauh lebih baik, selidiki data sebelum mengutak-atik model.
6. **Lakukan error analysis** (false negative dan false positive) sebelum menyimpulkan model "bagus".
7. **Hasil di data sintetis/smoke test tidak bermakna** dan tidak boleh dilaporkan sebagai performa model.
8. Jangan mengklaim peningkatan tanpa angka sebelum-sesudah dari run yang sama kondisinya (split, seed, hyperparameter).
9. Preprocessing tetap **minimal** untuk BERT: jangan hapus stopword, jangan stemming, jangan buang semua tanda baca. Emoji dan tanda baca bisa membawa sinyal sarkasme.
10. Kalau data imbalanced, gunakan `--class-weights` atau oversampling, dan sebutkan di laporan.

## 7. Aturan MPS / Mac dan CUDA / Colab

- Mac/MPS: jangan pakai `fp16=True`; `dataloader_num_workers=0`; mulai `batch_size=8–16`, `max_length=64–128`.
- Mac ini tanpa fan: untuk run panjang, ingatkan pemilik untuk memakai charger dan ventilasi, dan laporkan jika kecepatan turun drastis (throttling).
- Colab/CUDA: `fp16` otomatis aktif di T4, `dataloader_num_workers=2`; simpan checkpoint ke Drive karena runtime bisa mati, lalu lanjutkan dengan `--resume`.
- Device dipilih otomatis lewat `cyberbully.runtime.resolve_device` (`cuda` > `mps` > `cpu`); jangan hardcode.
- Selalu uji pipeline dengan `--subset` kecil sebelum run penuh dan laporkan waktu per langkah.
- Jika op tidak didukung MPS, andalkan `PYTORCH_ENABLE_MPS_FALLBACK=1`. Jangan menulis workaround rumit sebelum melapor.

## 8. Aturan notebook

- Nama: `NN_topik_snake_case.ipynb`. Satu notebook = satu tujuan.

  | File | Tujuan |
  |---|---|
  | `00_colab_setup` | menyiapkan runtime Colab, paket, Drive, dan split data |
  | `01_eda` | memahami data: label, panjang teks, duplikat, sampel |
  | `02_baseline_tfidf` | baseline + top fitur per kelas |
  | `03_error_analysis` | FN/FP model, pola error |
  | `04_model_comparison` | IndoBERT vs IndoBERTweet vs baseline |
  | `05_threshold_tuning` | PR curve, threshold dari validation set |
  | `06_colab_training` | smoke + full training di Colab lewat CLI, evaluasi val |
  | `99_report` | laporan utuh, memuat hasil (bukan training) |

- **Wajib bisa dipahami pemula ML/NLP:** setiap notebook memuat Tujuan, Prasyarat, Estimasi waktu, Glosarium, dan Ringkasan. Setiap sel kode didahului markdown yang menjelaskan apa yang dilakukan, kenapa, cara membaca output, dan apa yang terjadi bila gagal.
- `tests/test_notebooks.py` menegakkan struktur itu; notebook tanpa penjelasan akan menggagalkan test.
- Notebook memanggil `src/`, tidak menduplikasi logikanya.
- Training penuh tidak dijalankan di notebook lokal. Pengecualian Colab: notebook boleh memanggil `python -m cyberbully.train`, bukan menyalin kode training.
- Sebelum commit: **Restart & Run All** harus lolos. Notebook yang butuh model/data asli harus memberi pesan guard yang jelas bila belum ada, bukan crash.
- Output besar dibersihkan sebelum commit, kecuali yang menjadi bukti hasil di `99_report`.
- Jangan menyimpan data mentah atau teks pengguna asli di output notebook yang di-commit.

## 9. Data, privasi, dan etika

- Dataset dipakai untuk riset/edukasi. Patuhi lisensi dan ToS tiap dataset dan platform.
- Dataset proyek: `re_dataset.csv` (Ibrohim & Budi, 2019), lisensi **CC BY-NC-SA 4.0** — wajib atribusi, non-komersial, share-alike. Detail ada di `docs/dataset.md`.
- **Jangan scraping** Twitter/Instagram/TikTok. **Jangan mengunduh dataset** tanpa persetujuan pemilik repo. Yang boleh dibuat tanpa izin hanyalah data sintetis kecil untuk smoke test.
- Jangan commit data mentah, data hasil proses, atau model. Cek `.gitignore` sebelum `git add`.
- Jangan mencetak atau menyimpan username, nomor telepon, atau info pribadi yang ada di dataset. Anonimkan bila perlu.
- Data sintetis hanya boleh masuk **train**. Wajib lolos `scripts/check_synthetic.py` (tanpa PII, duplikat, atau overlap dengan val/test/eval) dan tidak boleh diklaim sebagai bukti performa.
- Model ini alat bantu moderasi, bukan alat penghukuman otomatis. Cantumkan keterbatasan (butuh konteks, bias dataset, sindiran yang lolos, false positive pada kata kasar akrab) di README dan laporan.
- `data/eval/implicit_eval.csv` ditulis manual. Jangan mengisinya dengan hasil generate otomatis tanpa label dari pemilik. Kalau diminta membantu menambah contoh, tandai sebagai *usulan* untuk direview.

## 10. API dan frontend

- API: `POST /predict?model=a|b` (body `{"text": str}`, 1–2000 karakter) mengembalikan `label`, `score`, `bully_probability`; `POST /compare` mengembalikan `a` dan `b`; `GET /health` mengembalikan `status`, `model_loaded`, dan `models` per A/B. Model A default `models/indobert_real`, B `models/indobert_aug`. Model belum lengkap harus menghasilkan **503**, bukan crash. Input tidak valid menghasilkan **422**.
- Model dimuat sekali saat startup, bukan per request.
- CORS hanya untuk origin dev (`http://localhost:5173`, `http://127.0.0.1:5173`). Jangan mengubahnya menjadi `*`.
- Frontend (`interface/`, Vite): React + TypeScript strict. URL API dari `VITE_API_URL`, default `http://localhost:8000`. Tangani state loading dan error. Jangan menampilkan stack trace ke pengguna.
- Perubahan kontrak API harus diikuti perubahan frontend, test, dan README dalam commit/PR yang sama.

## 11. Git

- Satu commit = satu perubahan logis. Format pesan: `type: ringkasan` (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`), contoh `fix: use processing_class in Trainer`.
- Jangan `git push`, `git reset --hard`, `git push --force`, atau menulis ulang history tanpa izin.
- Jangan commit: `data/raw/*`, `data/processed/*`, `models/*`, `out/`, `node_modules/`, `.venv/`, file `.env`, atau token.
- Jalankan `git status` dan lihat diff sebelum commit; pastikan tidak ada artefak yang ikut.

## 12. Batas keamanan

Dilarang tanpa izin eksplisit:
- `sudo`, `rm -rf` di luar folder repo, mengubah Python global/sistem, mengubah file shell (`~/.zshrc`, dll.)
- `brew install/upgrade/uninstall`, meng-upgrade atau meng-uninstall paket di `ml-lab` yang bukan kebutuhan langsung tugas
- Membaca atau mencetak file rahasia (`~/.ssh`, `.env`, kredensial, token)
- Mengirim isi repo atau data ke layanan luar selain unduhan model dari `huggingface.co` yang diminta
- Menjalankan proses di background yang tidak kamu hentikan setelah selesai (uvicorn, vite, dll.)

## 13. Cara bekerja

1. **Pahami dulu**: baca file terkait sebelum mengubah. Jangan berasumsi struktur; cek dengan `ls`/`cat`.
2. **Rencana singkat** untuk tugas non-trivial: sebutkan file yang akan diubah dan alasannya, lalu kerjakan.
3. **Perubahan minimal**: jangan refactor besar atau mengganti library tanpa diminta.
4. **Verifikasi dengan menjalankan**: `pytest`, jalankan script yang diubah, uji endpoint dengan `curl`. Kode yang tidak dijalankan harus dilabeli "belum diuji".
5. **Lapor jujur**: kalau gagal, tampilkan error aslinya. Jangan mengarang output, metrik, atau hasil, dan jangan mengklaim berhasil tanpa bukti.
6. **Berhenti dan tanya** jika: ada keputusan dengan trade-off nyata (pilih dataset, pemetaan label, ubah arsitektur), tindakan butuh izin di bagian 12, atau persyaratan ambigu. Ajukan satu pertanyaan yang jelas, lengkap dengan opsi dan rekomendasimu.
7. Kalau menemukan bug di kode yang ada, perbaiki dengan perubahan kecil dan catat: file, masalah, penyebab, perbaikan.

## 14. Definition of done (per tugas)

- Perintah yang relevan sudah dijalankan dan outputnya dilampirkan
- `pytest -q` hijau
- Tidak ada artefak data/model/`node_modules` di staging git
- README atau docstring diperbarui jika perilaku atau perintah berubah
- Hal yang belum terverifikasi dinyatakan eksplisit

## 15. Format laporan setelah tugas

1. Ringkasan satu paragraf: apa yang selesai, apa yang tidak
2. Perubahan: daftar file baru/diubah dengan satu baris alasan
3. Bukti: perintah yang dijalankan dan hasil pentingnya
4. Bug/masalah ditemukan: file, penyebab, perbaikan
5. Belum terverifikasi / butuh keputusan pemilik
6. Saran langkah berikutnya (maksimal 3)

## 16. Status project (perbarui oleh agent di akhir tiap sesi, singkat)

- [x] Audit environment `ml-lab` disetujui
- [x] Pipeline tervalidasi di MPS (smoke tiny model; metrik tidak bermakna)
- [x] Dataset dipilih dan label dipetakan (keputusan pemilik)
- [x] Baseline TF-IDF selesai (F1 val 0,881)
- [x] Fine-tuning IndoBERT A selesai (3 epoch, F1 val 0,926); B menunggu training ulang
- [ ] Augmentasi sintetis 15k siap; model B (real+synthetic) belum ditraining
- [ ] Eval set manual ≥ 200 contoh (baru 20 usulan, belum direview)
- [ ] Error analysis selesai (notebook siap; final setelah eval set)
- [x] API + frontend demo dua model (A/B) selesai; butuh model untuk berjalan
- [ ] `99_report` terisi (template sudah memuat validation; test belum final)

Catatan 2026-11-25: artefak model, out/, data/processed/, dan CSV sintetis direset. Angka di atas adalah referensi run sebelumnya; ikuti docs/guide.md untuk reproduksi. Raw data dan eval set tetap ada.

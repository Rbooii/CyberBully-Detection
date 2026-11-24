# Memory — CyberBully

Log keputusan dan status untuk sesi agent berikutnya. Append-only, entri terbaru
di bawah. Aturan kerja ada di `agents.md`, cara operasional di `agent/skills.md`.

## 2026-11-23 — Audit environment & scaffold awal

**Keputusan**

- `ml-lab` = venv buatan uv di `/Users/arcozkwn/.venvs/ml`, Python 3.12.16.
  Bukan conda/pyenv: keduanya tidak terpasang.
- Frontend akan berada di `interface/` (Vite + React + TS), menggantikan
  `frontend/` yang tertulis di `agents.md` §3/§4/§10.
- Dokumentasi agent memakai dua file datar: `agent/skills.md` + `agent/memory.md`.

**Alasan**

- Path env ditemukan lewat kernelspec Jupyter "Python (ML Lab)"; tidak ada di
  PATH sehingga `conda env list`/`pyenv versions` tidak menemukannya.
- Folder `frontend/` tidak pernah dibuat; pemilik repo meminta `interface/`
  khusus untuk implementasi frontend ringan.
- Dua file datar lebih mudah dirawat daripada subfolder kosong
  `agent/skills/` dan `agent/memory/` yang sebelumnya ada.

**Bukti**

- Python 3.12.16, torch 2.15.0, MPS `available=True`, matmul MPS berhasil.
- Instalasi `.[api,dev]` menarik transformers 5.24.0, datasets, accelerate,
  fastapi 0.165.0, pytest 9.2.0.
- `python -m pytest`: 12 passed in 0.74s.
- Smoke test CLI: CSV sintetis 42 baris → 40 setelah dedup → train 32 / val 4 /
  test 4, tiap split memuat kedua kelas.

**Terbuka / belum terverifikasi**

- Belum ada dataset asli dan `data/eval/implicit_eval.csv`; belum ada
  `train.py`, `evaluate.py`, `predict.py`, API, maupun frontend.
- Dedup masih exact setelah normalisasi. Teks "nyaris sama" (typo, parafrase)
  belum dicegah; ini celah terhadap `agents.md` §6.1 yang perlu diputuskan
  pemilik (mis. MinHash/`difflib`).
- `notebooks/01_experiment.ipynb` masih 0 byte dan namanya tidak sesuai
  konvensi `NN_topik_snake_case.ipynb`.
- `agents.md` di root memakai huruf kecil, sedangkan §3 menulis `AGENTS.md`.
  Belum di-rename agar tidak memutus referensi yang ada.
- Transformers terpasang 5.24.0; kompatibilitas kode training (Trainer,
  tokenizer, `datasets`) belum diuji karena `train.py` belum ada.

**Langkah berikutnya**

1. Pilih dataset dan petakan label bersama pemilik, lalu jalankan
   `cyberbully.data` pada data asli.
2. Bangun `train.py` (HF Trainer, MPS) dan uji `--subset` kecil dulu.
3. Siapkan baseline TF-IDF + Logistic Regression sebelum menyimpulkan apa pun
   tentang IndoBERT.

## 2026-11-24 (sesi 2) — Dataset, training, dan Colab

**Keputusan**

- Dataset: `re_dataset.csv` dari Ibrohim & Budi (2019), mirror Kaggle
  `ilhamfp31/indonesian-abusive-and-hate-speech-twitter-text`, lisensi
  **CC BY-NC-SA 4.0**. SHA-256 lokal sama persis dengan repo asli:
  `44c04e31ad4b7ee4a95f1884e7af4da2c44b69762143eb2de0ede7f90502735e`.
- Label: `bully = HS == 1 OR Abusive == 1` (union). Kolom `HS`/`Abusive`
  disimpan untuk analisis subgroup.
- Frontend tetap di `interface/`; GitHub belum punya remote dan akan di-push
  sendiri oleh pemilik.
- Notebook 00/01/06 dibuat; training Colab hanya memanggil CLI, bukan logika
  baru di notebook.

**Alasan**

- Union mencakup hinaan langsung maupun ujaran kebencian; HS-only melewatkan
  hinaan, Abusive-only melewatkan kebencian tanpa kata kasar.
- File asli bukan UTF-8 murni dan menyimpan emoji sebagai escape; tanpa repair,
  sinyal emoji hilang. latin-1 tidak dipakai karena merusak teks UTF-8 valid.
- Test set harus tetap perawan sampai laporan; `evaluate.py` memaksa
  `--confirm-test` dan threshold eksplisit.

**Bukti**

- `pytest`: 35 passed.
- Split data asli: 12.997 baris → train 10.397 / val 1.300 / test 1.300;
  positif 7.224.
- Smoke training tiny model di MPS: 128 baris, 1 epoch, ±4 detik train +
  ±1 detik eval; device terdeteksi `mps`, `fp16=False`.
- `evaluate.py --split val` pada model smoke berjalan; `--split test` tanpa
  `--confirm-test` keluar dengan kode 2.
- Ketiga notebook dieksekusi lokal lewat nbclient dengan kernel `ml`; semua sel
  lolos tanpa error. Output tidak disimpan.

**Terbuka / belum terverifikasi**

- Full training IndoBERT belum dijalankan; belum ada metrik yang bisa dilaporkan.
- Baseline TF-IDF belum dibuat.
- Threshold tuning dan evaluasi test belum dilakukan.
- Colab belum diuji di runtime Google (perlu akun/GPU); baru diuji secara lokal.
- Dedup fuzzy (teks nyaris sama) belum ada; 82 run escape tidak valid dibiarkan.
- `notebooks/01_experiment.ipynb` (0 byte) sudah dihapus, diganti `01_eda.ipynb`.
- Repo belum punya remote; panduan Colab memakai placeholder `REPO_URL`.

**Langkah berikutnya**

1. Full training IndoBERT di Colab (atau MPS semalam), catat waktu per epoch.
2. Baseline TF-IDF + Logistic Regression pada split yang sama.
3. Threshold tuning dari `val_predictions.csv`, baru evaluasi test sekali.

## 2026-11-24 (sesi 3) — Baseline, API, frontend, dan Colab

**Keputusan**

- Repo remote aktif: `https://github.com/Rbooii/CyberBully-Detection.git`
  (public); commit lama sudah di-push.
- Training final 3 epoch dipindahkan ke **Colab T4**. Training lokal di M3
  berhenti di tengah epoch 2 (SIGTERM, tanpa traceback/OOM); checkpoint epoch 1
  dipakai sebagai model demo **preliminary**.
- Eval set manual berisi 20 contoh **usulan** (`status=usulan`), bukan label
  final. `evaluate.py` melewati baris usulan.
- Frontend di `interface/` memakai Vite + React + TS strict, desain riset/
  kredibel, `VITE_API_URL`, state loading/error.

**Bukti**

- Baseline validation: threshold 0,40; accuracy 0,865; precision 0,860;
  recall 0,903; F1 0,881.
- IndoBERT epoch 1: threshold 0,50; accuracy 0,907; precision 0,939;
  recall 0,891; F1 0,9141. Threshold tuned 0,34: F1 0,9146, recall 0,911,
  precision 0,918. Checkpoint: `models/indobert/checkpoints/checkpoint-650`.
- `pytest`: 52 passed. `npm run build` sukses (TS strict).
- API dengan checkpoint: `/health` loaded=true; prediksi hinaan 0,993;
  ucapan semangat 0,057; input kosong 422. UI diuji di browser desktop/mobile.
- Temuan kualitatif: sindiran "Wah pintar sekali, sampai salah dua kali."
  diprediksi non-bully oleh checkpoint epoch 1 (false negative).
- Notebook 00–06 dan 99 lolos eksekusi lokal lewat kernel `ml`; output dibersihkan.

**Terbuka / belum terverifikasi**

- Full 3 epoch di Colab belum dijalankan; angka final dan test set belum ada.
- Eval set 20 usulan belum direview; target ≥200 baris final.
- Threshold 0,34 berasal dari model 1 epoch; harus dihitung ulang dari model final.
- `models/indobert/val_metrics.json` saat ini milik epoch 1, bukan model final.
- Panduan Colab belum diuji di runtime Google yang sebenarnya.

**Langkah berikutnya**

1. Push kode terbaru, lalu jalankan 00 + 06 di Colab (3 epoch, checkpoint ke Drive).
2. Unduh model final, evaluasi validation, tuning threshold, lalu test sekali.
3. Review 20 usulan eval set; isi hingga ≥200 baris final sebelum laporan.

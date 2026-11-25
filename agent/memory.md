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

## 2026-11-25 (sesi 4) — Model final 3 epoch dan data sintetis

**Keputusan**

- Model final 3 epoch dari Colab T4 sudah diunduh ke `models/indobert`; ini
  model yang dipakai API/frontend, bukan checkpoint epoch 1 lagi.
- Eval set manual tetap 20 usulan; belum direview dan belum dipakai untuk
  evaluasi final.
- Menambah 15k data sintetis untuk augmentasi train: 9.000 positif
  (sindiran/merendahkan/satir) + 6.000 hard negative (kasar akrab, kritik,
  netral, pujian). Hanya train; val/test tetap data asli.
- Generator memakai hybrid: seed tulis tangan + pola/slot, deterministik dengan
  seed 42. CSV gitignored; generator/validator di-commit.

**Bukti**

- Model final validation (threshold 0,5): accuracy 0,9185; precision 0,9339;
  recall 0,9184; F1 0,9261; CM [[530,47],[59,664]]. Threshold 0,42: F1 0,9292,
  recall 0,9253, precision 0,9331.
- API dengan model final: hinaan p=0,999; sindiran "Wah pintar sekali..." p=0,048
  (tetap false negative).
- `pytest`: 58 passed.
- Sintetis: 15.000 baris, nol duplikat, nol PII, nol overlap dengan
  train/val/test/eval. Median 9 kata (data asli 15).
- Augmented train: 25.397 baris (10.397 real + 15.000 synthetic), 14.779 positif
  / 10.618 negatif. Smoke training `--train-file` berhasil di MPS.
- Generator/validator: `scripts/generate_synthetic.py`,
  `scripts/check_synthetic.py`, `scripts/augment_train.py`.

**Terbuka / belum terverifikasi**

- Model B (real + 15k sintetis) belum ditraining; belum ada bukti augmentasi
  membantu di validation.
- Eval set final ≥200 belum ada; test set belum dievaluasi.
- Data sintetis berbasis template, lebih pendek dari tweet asli, dan labelnya
  berasal dari aturan generator; bisa memicu overfit pola.
- Threshold 0,42 harus dihitung ulang untuk model B jika dipakai.

**Langkah berikutnya**

1. Generate + validasi + augmentasi di Colab, lalu training model B dengan
   `--train-file data/processed/train_augmented.csv`.
2. Bandingkan A vs B di validation; pilih berdasarkan F1 dan subgroup, bukan eval
   set/test.
3. Review eval set hingga ≥200 final, baru evaluasi test sekali dan isi laporan.

## 2026-11-25 (sesi 5) — Reset artefak dan guide dari nol

**Keputusan**

- Atas permintaan pemilik, semua artefak turunan dihapus: isi `models/`, `out/`,
  `data/processed/`, CSV `data/synthetic/`, `interface/node_modules`, dan
  `interface/dist`.
- `data/raw/re_dataset.csv`, `data/eval/`, kode, docs, dan `.gitkeep`
  dipertahankan.
- Dibuat `docs/guide.md` (end-to-end dari nol) dan
  `scripts/reset_generated.py` (dry-run default, `--yes` untuk hapus).
- Angka hasil lama tetap dicatat sebagai referensi, bukan jaminan.

**Bukti**

- `reset_generated.py --yes`: 31 path dihapus, termasuk model 487 MB dan
  `node_modules` 88 MB.
- `pytest`: 62 passed tanpa model/data processed.
- Sisa direktori: hanya `.gitkeep`, `data/synthetic/README.md`, raw data, dan eval.
- Model final tidak ada lagi di laptop; API akan 503 sampai training ulang.

**Terbuka**

- Belum ada model/metrik lokal setelah reset; semua langkah harus diulang dari
  pipeline data.
- Eval set masih 20 usulan; test belum dievaluasi.
- Guide belum diuji dengan eksekusi penuh dari kondisi kosong (baru ditulis).

**Langkah berikutnya**

1. Ikuti `docs/guide.md` dari langkah 1; mulai dari pipeline data.
2. Jalankan smoke, lalu full training di Colab; unduh model.
3. Lanjutkan evaluasi validation, threshold, eval set, test sekali, laporan.

## 2026-11-25 (sesi 6) — Dua model A/B dan guide Colab full training

**Keputusan**

- Output dua model: A real-only `models/indobert_real`, B asli+sintetis
  `models/indobert_aug`.
- Satu API memuat keduanya: `/predict?model=a|b`, `/compare`, `/health.models`.
- Frontend menampilkan dua panel sejajar; selisih probabilitas ditampilkan tanpa
  klaim otomatis pemenang.
- Test dievaluasi sekali per model, threshold masing-masing dari validation.
- Guide khusus: `docs/colab_full_training.md`.

**Bukti**

- `pytest`: 62 passed (termasuk API dua model).
- `npm run typecheck/build/lint`: sukses.
- API fake: `/health` models a/b true; `/compare` mengembalikan dua hasil.
- Screenshot UI compare: `out/ui_compare.png` (model palsu, bukan performa).
- API tests mencakup: satu model hilang → 503, model key invalid → 422,
  payload invalid → 422, CORS.

**Terbuka / belum diverifikasi**

- Model A/B asli belum dilatih ulang setelah reset; API belum diuji dengan model
  nyata dua folder.
- Angka B belum ada; perbandingan test A/B belum dijalankan.
- Eval set masih 20 usulan; test belum dievaluasi.
- Screenshot UI memakai fake predictor, bukan model asli.

**Langkah berikutnya**

1. Jalankan `docs/colab_full_training.md`: train A, generate synthetic, train B.
2. Unduh kedua model, evaluasi validation, tuning threshold A/B.
3. Test sekali per model, isi laporan, uji API `/compare` + frontend dengan model
   asli, commit/push.

## 2026-11-25 (lanjutan) — B v1 gagal di kasus sulit, ganti data dan B2

**Temuan**

- B v1 benar-benar memakai train augmented (25.397 baris) dan test F1 0,9293;
  A test F1 0,9254. Secara agregat B sedikit lebih baik.
- Namun B v1 gagal di kasus yang menjadi inti proyek:
  - backhanded compliment: p≈0,000
  - sarkasme karya: p≈0,000
  - gaslighting: p≈0,0005
  - body shaming: p≈0,000
  - subtweet: p≈0,9999 (justru berhasil)
- Penyebab: data sintetis v1 tidak punya kategori tersebut, dan frasa
  "cuma bercanda" dilatih sebagai negatif `kasar_akrab`. Ini kontraproduktif
  untuk gaslighting.
- API juga masih memakai threshold 0,5; B v1 dibekukan di 0,17.

**Keputusan**

- Hapus model B v1, `out/model_b`, CSV synthetic v1, dan train_augmented v1.
- Ganti dengan 20.000 baris: 14.000 positif (termasuk lima kategori sulit) +
  6.000 hard negative (pujian tulus, permintaan maaf tulus, perhatian tulus,
  kritik, netral, becanda akrab).
- Tambah 30 contoh eval `usulan` untuk lima kategori; total eval set 50 usulan.
- Train ulang **B2 saja**; A tetap.
- `Predictor` sekarang membaca `threshold.json` dari folder model; API
  mengembalikan `threshold` dan `/health` menampilkan `thresholds`.

**Bukti**

- Synthetic 20k: 0 duplikat, 0 PII, 0 overlap dengan train/val/test/eval.
- Augmented train: 30.397 baris (10.397 real + 20.000 synthetic); 19.779
  positif / 10.618 negatif.
- `pytest`: 68 passed; frontend typecheck/build/lint sukses.
- `models/indobert_aug` dan `out/model_b` sudah dihapus; A dan threshold A 0,42
  tetap.

**Terbuka**

- B2 belum ditraining; belum ada bukti kategori sulit membaik.
- Eval set 50 usulan belum direview; target ≥200 final.
- Test set sudah pernah dipakai A dan B v1; evaluasi B2 akan menjadi penggunaan
  tambahan dan harus ditulis sebagai keterbatasan.
- API threshold server lama perlu restart agar membaca threshold baru.

**Langkah berikutnya**

1. Train B2 di Colab dengan `train_augmented.csv` 30.397 baris.
2. Unduh B2, evaluasi validation, threshold, eval set per kategori.
3. Test B2 sekali; bandingkan A/B2 dan tulis hasil apa adanya.

## 2026-11-25 (lanjutan) — B2 selesai, threshold boundary diperbaiki

**Temuan**

- B2 (20k targeted, 30.397 train) mendeteksi lima contoh sulit dengan p≈1,0:
  subtweet, backhanded, sarkasme karya, gaslighting, body shaming. A tetap gagal
  di empat dari lima (p 0,002–0,11); hanya subtweet yang juga dikenali B2.
- F1 validation B2 pada 0,5 = 0,917 (P 0,922, R 0,913), lebih rendah dari A
  (0,926 / 0,929 tuned). Trade-off: B2 jauh lebih baik di kasus sulit, lebih
  rendah secara agregat.
- `choose_threshold` memilih 0,05 karena itu batas bawah grid; F1 0,05 vs 0,5
  hanya berbeda 0,004 dan precision turun (0,911 vs 0,922). Ini artefak, bukan
  optimum nyata.
- API semula memakai threshold 0,5 untuk A/B karena belum membaca file; sudah
  diperbaiki.

**Keputusan**

- `choose_threshold` sekarang fallback ke 0,5 jika optimum mentok di boundary
  atau gain F1 < 0,002 dari default. A tetap 0,42 (interior, gain cukup).
- B2 threshold deploy = 0,5. File `threshold.json` di folder model dibaca API.
- Test B2 sudah tercatat pada 0,05 (F1 0,919); test pada 0,5 tidak dijalankan
  ulang agar tidak menjadi evaluasi kedua.

**Bukti**

- `pytest`: 69 passed.
- API `/health` dengan model nyata: thresholds A 0,42, B 0,5.
- API `/compare` gaslighting: A p=0,110 non-bully; B p=0,999 bully.
- Threshold B di `out/model_b/threshold.json` dan `models/indobert_aug/threshold.json`
  sekarang 0,5, fallback `boundary`, kandidat 0,05.

**Terbuka**

- Eval set 50 masih usulan; akurasi per kategori belum dihitung.
- Test B2 pada 0,5 belum ada; laporan harus membedakan test 0,05 (tercatat) dan
  threshold deploy 0,5.
- B2 masih lebih rendah dari A pada F1 agregat; keputusan model utama menunggu
  evaluasi per kategori.
- Test set sudah dipakai A dan B2 (0,05); keterbatasan metodologis harus dicatat.

**Langkah berikutnya**

1. Review 50 eval usulan menjadi `final`, evaluasi A/B2 per kategori.
2. Putuskan model utama: A (agregat lebih baik) atau B2 (kasus sulit lebih baik).
3. Tulis laporan dengan trade-off dan keterbatasan test; jangan mengulang test
   tanpa alasan yang dicatat.

## 2026-11-25 (lanjutan) — Evaluasi eval set dan redesign frontend

**Temuan**

- Eval set setelah review: 40 `final`, 10 `usulan` (gaslighting 5, sarkasme karya
  3, body shaming 1, becanda akrab 1).
- `evaluate.py` bug: default threshold 0,5 dipaksa dan mengabaikan
  `threshold.json` model. Sudah diperbaiki; A dievaluasi di 0,42, B2 di 0,5.
- Hasil eval set 40 final:
  - A: accuracy 0,500; P 1,000; R 0,259; F1 0,412.
  - B2: accuracy 0,850; P 0,839; R 0,963; F1 0,897.
- Per kategori: B2 unggul di pujian menyindir, body shaming, sarkasme karya,
  subtweet, dan merendahkan. A hanya unggul/bersih di hinaan langsung, kritik,
  netral, opini, keluhan. B2 menimbulkan false positive pada kritik/netral.
- Gaslighting belum dihitung karena semua barisnya masih `usulan`.
- File eval CSV sempat rusak saat disimpan (spasi sebelum quote); sudah
  dirapikan tanpa mengubah isi/label.

**Frontend**

- Redesign mengikuti `agent/design.md`, `agent/DESIGN_GUIDE.md`, dan
  `agent/globals.css`: Geist Sans/Mono, token OKLCH monokrom, sidebar desktop,
  drawer mobile, theme switch, tombol ink, panel hasil flat, mono metadata.
- Light/dark dan mobile sudah diuji lewat browser; build/typecheck/lint sukses.
- Halaman memakai `/compare` dan menampilkan threshold tiap model.

**Terbuka**

- 10 eval usulan belum final; gaslighting belum terukur.
- Test B2 pada 0,5 belum ada; test B2 tercatat pada 0,05. Ini keterbatasan.
- Model utama belum diputuskan: A unggul agregat, B2 unggul kasus sulit.
- `99_report` sudah memuat tabel eval set; keputusan model utama belum ditulis.

**Langkah berikutnya**

1. Review 10 usulan tersisa, terutama gaslighting; evaluasi ulang eval set.
2. Pilih model utama sesuai tujuan proyek dan tulis trade-off.
3. Isi `99_report`, update README, commit/push.

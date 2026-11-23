# CyberBully Detection (Bahasa Indonesia)

Deteksi cyberbullying pada teks bahasa Indonesia dengan fine-tuning IndoBERT.
Task klasifikasi biner: `bully` (1) / `non-bully` (0), termasuk tantangan
sindiran tanpa kata kasar.

**Status:** tahap scaffold. Belum ada dataset, model, maupun hasil metrik.
Angka apa pun dari data sintetis hanyalah smoke test dan tidak boleh dilaporkan
sebagai performa model.

## Environment

Training dan inference berjalan di venv `ml-lab` (uv, Python 3.12):

```bash
uv pip install --python /Users/arcozkwn/.venvs/ml/bin/python -e ".[api,dev]"
```

Selalu set fallback MPS sebelum training/inference:

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

## Perintah

```bash
# data: normalisasi, dedup, split train/val/test (train 80 / val 10 / test 10)
/Users/arcozkwn/.venvs/ml/bin/python -m cyberbully.data \
    --input data/raw/<file>.csv --text-col <kolom_teks> --label-col <kolom_label> \
    --positive bully

# test
/Users/arcozkwn/.venvs/ml/bin/python -m pytest -q
```

Perintah training, evaluasi, API, dan frontend menyusul saat modulnya ada
(lihat `agents.md` §4). Frontend berada di `interface/` (Vite + React + TS).

## Struktur singkat

```
src/cyberbully/   logika reusable (config, preprocess, data)
data/raw/         dataset asli, read-only, gitignored
data/processed/   hasil split, gitignored
data/eval/        test set manual (implicit_eval.csv), di-commit
agent/            skills.md (cara kerja) + memory.md (log keputusan)
interface/        frontend
notebooks/        eksplorasi & laporan
```

## Aturan data

- Dedup dan normalisasi dilakukan **sebelum** split; tidak boleh ada teks yang
  muncul di train dan test.
- Test set disentuh sekali untuk laporan akhir; threshold dan hyperparameter
  diambil dari validation set.
- Preprocessing minimal: stopword, tanda baca, dan emoji dipertahankan.

## Keterbatasan & etika

Model ini alat bantu moderasi, bukan penghukum otomatis. Konteks percakapan,
bias dataset, sindiran yang lolos, dan kata kasar akrab (mis. bercanda antar
teman) dapat menghasilkan false negative maupun false positive. Jangan dipakai
untuk keputusan otomatis terhadap individu.

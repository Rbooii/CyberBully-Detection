# Eval set manual

`implicit_eval.csv` adalah test set manual untuk kasus sulit, terutama sindiran
tanpa kata kasar. File ini **ditulis manusia**, bukan hasil generate otomatis.

## Kolom

| Kolom | Arti |
|---|---|
| `text` | satu komentar |
| `label` | `1` bully, `0` non-bully |
| `category` | kategori untuk akurasi per kelompok |
| `status` | `usulan` (belum direview) atau `final` (sudah disetujui pemilik) |

## Status saat ini

20 baris pertama adalah **usulan** dan semuanya berstatus `usulan`.
`cyberbully.evaluate` melewati baris berstatus `usulan`, sehingga angka eval set
tidak muncul sampai Anda review.

## Cara review

1. Baca setiap baris dan putuskan label yang benar.
2. Ubah `status` menjadi `final` hanya untuk baris yang sudah Anda setujui.
3. Tambah contoh sampai minimal 200 baris final.
4. Jangan menyalin komentar dari train/validation/test; eval set harus baru.

Jangan mengisi file ini dengan prediksi model. Tujuannya mengukur model pada
kasus yang belum pernah dilihat, bukan mengulang jawaban model.

## Menjalankan evaluasi

```bash
python -m cyberbully.evaluate --split val \
    --model-dir models/indobert \
    --implicit-eval data/eval/implicit_eval.csv
```

Hasil per kategori ditulis ke `out/implicit_metrics.json` (gitignored).

## Lisensi

Teks di file ini ditulis untuk demo, bukan diambil dari dataset. Dataset utama
tetap CC BY-NC-SA 4.0; jangan menambahkan data pengguna nyata tanpa izin.

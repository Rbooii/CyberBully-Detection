# Synthetic data

Folder ini berisi data sintetis yang dihasilkan `scripts/generate_synthetic.py`.
CSV **tidak di-commit**; yang di-commit hanya generator, seed, dan dokumentasi.

## Isi

15.000 baris, seed 42:

| Kategori | Label | Jumlah |
|---|---|---|
| sindiran | 1 | 4.000 |
| merendahkan | 1 | 3.000 |
| satir | 1 | 2.000 |
| kasar_akrab | 0 | 2.000 |
| kritik | 0 | 1.500 |
| netral | 0 | 1.500 |
| pujian | 0 | 1.000 |

Total 9.000 positif dan 6.000 hard negative.

## Skema

| Kolom | Arti |
|---|---|
| `text` | teks sintetis |
| `label` | 1 bully, 0 non-bully |
| `category` | kategori generator |
| `origin` | `seed` atau `template` |

## Aturan

- **Hanya untuk train.** Jangan pernah menambahkan ke validation/test.
- Jalankan `scripts/check_synthetic.py`; harus nol duplikat, nol PII, nol overlap
  dengan train/val/test/eval.
- Data ini bukan pengganti dataset asli; ia augmentasi.
- Jangan memakai hasil model pada data sintetis sebagai bukti performa.
- Teks dibuat untuk riset moderasi; tanpa nama, akun, telepon, atau slur.

## Reproduksi

```bash
python scripts/generate_synthetic.py
python scripts/check_synthetic.py
python scripts/augment_train.py
```

Output: `data/synthetic/synthetic_train.csv` dan
`data/processed/train_augmented.csv` (keduanya gitignored).

## Batasan

- Dibuat dari pola/template + 35 seed tulis tangan, bukan 15.000 kalimat tulisan
  manusia independen.
- Median 9 kata, lebih pendek dari data asli (median 15 kata).
- Distribusi dan gaya bahasa tidak identik dengan tweet nyata.
- Label ditentukan oleh aturan generator, bukan anotator manusia.
- Karena itu, klaim akhir tetap dari test set nyata dan eval set manual.

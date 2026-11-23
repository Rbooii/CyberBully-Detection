# Dataset

## Identitas

| Item | Nilai |
|---|---|
| Nama | Indonesian Abusive and Hate Speech Twitter Text |
| Mirrors Kaggle | <https://www.kaggle.com/datasets/ilhamfp31/indonesian-abusive-and-hate-speech-twitter-text> |
| Sumber asli | <https://github.com/okkyibrohim/id-multi-label-hate-speech-and-abusive-language-detection> |
| File | `re_dataset.csv` |
| Ukuran | 1.858.473 byte, 13.169 baris, 13 kolom |
| SHA-256 | `44c04e31ad4b7ee4a95f1884e7af4da2c44b69762143eb2de0ede7f90502735e` |
| Lisensi | **CC BY-NC-SA 4.0** |

SHA-256 file lokal sudah diverifikasi sama dengan `re_dataset.csv` di repo asli.

## Sitasi wajib

> Muhammad Okky Ibrohim and Indra Budi. 2019. Multi-label Hate Speech and
> Abusive Language Detection in Indonesian Twitter. In *ALW3: 3rd Workshop on
> Abusive Language Online*, 46–57.

## Skema

`Tweet` berisi teks; kolom lain adalah label biner 0/1:

| Kolom | Arti |
|---|---|
| `HS` | ujaran kebencian |
| `Abusive` | bahasa kasar/hinaan |
| `HS_Individual`, `HS_Group` | target individu / kelompok |
| `HS_Religion`, `HS_Race`, `HS_Physical`, `HS_Gender`, `HS_Other` | kategori sasaran |
| `HS_Weak`, `HS_Moderate`, `HS_Strong` | intensitas |

## Keputusan label proyek

`bully = 1` bila **`HS == 1` atau `Abusive == 1`**, selain itu `0`.

Alasan: cyberbullying mencakup hinaan langsung maupun ujaran kebencian.
Membatasi ke `HS` saja akan melewatkan hinaan tanpa target kebencian; `Abusive`
saja melewatkan ujaran kebencian yang tidak terdeteksi sebagai kata kasar.
Kolom `HS` dan `Abusive` tetap disimpan lewat `--keep-cols` untuk analisis
subgroup dan error analysis.

Setelah repair encoding dan dedup: **12.997 baris**, 7.224 positif (55,6%) dan
5.773 negatif.

## Kualitas data yang perlu diketahui

- File bukan UTF-8 murni: 953 karakter rusak. `--encoding auto` menggantinya
  dengan `?` dan memberi peringatan; tidak memakai latin-1 agar teks UTF-8 yang
  valid tidak berubah menjadi mojibake.
- 1.435 baris menyimpan emoji sebagai escape literal (`\xf0\x9f...`).
  `normalize_text` memperbaiki 1.391 di antaranya; 82 run yang tidak membentuk
  UTF-8 valid dibiarkan.
- 172 duplikat setelah normalisasi dibuang sebelum split.
- Penulis asli sudah mengganti username dan URL menjadi token `USER`/`URL`.

## Aturan penggunaan

- **Jangan commit** file mentah atau hasil proses; keduanya ada di `.gitignore`.
- **Non-komersial** (NC): proyek ini untuk riset/edukasi. Demo tidak boleh
  dikomersialkan.
- **ShareAlike** (SA): bila dataset olahan dibagikan, ikuti lisensi yang sama.
- Cantumkan sitasi di README, notebook, dan laporan.
- Jangan mencetak isi tweet mentah ke output notebook yang di-commit.

## Reproduksi

```bash
cp ~/Downloads/re_dataset.csv data/raw/re_dataset.csv
python -m cyberbully.data \
    --input data/raw/re_dataset.csv \
    --text-col Tweet \
    --label-col HS Abusive \
    --positive 1 \
    --label-mode any \
    --keep-cols HS Abusive
```

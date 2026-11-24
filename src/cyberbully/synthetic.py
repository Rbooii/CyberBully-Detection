"""Generator dan validator data sintetis untuk augmentasi train.

Data sintetis hanya boleh masuk train. Validation, test, dan eval set manual
tidak boleh menerima baris sintetis. Semua teks ditulis untuk riset moderasi:
tanpa nama asli, nomor telepon, akun, atau slur eksplisit.
"""

from __future__ import annotations

import random
import re
from typing import Mapping, Sequence

import pandas as pd

from .config import LABEL_COLUMN, SEED, TEXT_COLUMN
from .preprocess import normalize_text

ORIGIN_COLUMN = "origin"
CATEGORY_COLUMN = "category"

DEFAULT_COUNTS: dict[str, tuple[int, int]] = {
    "sindiran": (1, 4_000),
    "merendahkan": (1, 3_000),
    "satir": (1, 2_000),
    "kasar_akrab": (0, 2_000),
    "kritik": (0, 1_500),
    "netral": (0, 1_500),
    "pujian": (0, 1_000),
}

SLOTS: dict[str, list[str]] = {
    "pujian": ["hebat", "pintar", "cerdas", "profesional", "rajin", "teliti", "berbakat", "matang", "konsisten", "siap"],
    "kegagalan": ["salah lagi", "lupa instruksi", "telat lagi", "nggak baca brief", "hasilnya berantakan", "bikin masalah lagi", "nggak nyambung", "kelewatan detail penting", "kerjaannya belum selesai", "malah nambah kerjaan"],
    "perilaku": ["nyalahin orang", "cari alasan", "sok sibuk", "nggak mau dengar", "minta dipuji", "menunda kerjaan", "bikin ribet", "nggak jujur"],
    "hasil": ["dianggap hebat", "dipuji atasan", "dapat pujian", "dianggap korban", "disalahkan orang lain", "tetap dibela", "dikasih kesempatan lagi"],
    "klaim": ["sudah berpengalaman", "paham semuanya", "bisa selesai cepat", "ahli strategi", "paling teliti", "sudah biasa memimpin", "paling profesional", "paling paham"],
    "kenyataan": ["baru mulai pun bingung", "hasilnya belum ada", "deadline lewat", "kerjanya masih berantakan", "detail kecil pun terlewat", "masih perlu dibimbing", "presentasinya belum siap", "pertanyaan dasar pun bingung"],
    "aktivitas": ["ikut rapat", "presentasi", "ambil tanggung jawab", "minta proyek besar", "sok memimpin", "ngurus tim", "tampil di depan", "bicara di forum", "ngatur jadwal", "jadi perwakilan tim"],
    "sikap": ["bangga", "tenang saja", "nggak merasa salah", "santai", "merasa paling benar", "tersenyum saja", "cuek", "tanpa rasa bersalah"],
    "celaan": ["nggak cocok kerja di sini", "cuma bikin lambat", "nggak pernah siap", "terlalu banyak alasan", "nggak bisa diandalkan", "beban tim", "nggak pantas dapat kesempatan", "sulit diajak kerja sama", "cuma bisa ngomong", "nggak punya kontribusi", "terlalu sering minta bantuan", "nggak pernah belajar dari kesalahan", "cuma menambah masalah", "nggak bisa menjaga komitmen"],
    "target": ["orang", "orang baru", "anggota tim", "orang yang sok sibuk", "orang yang selalu beralasan", "orang yang baru gabung"],
    "hasil_merendahkan": ["didengar", "dipercaya", "berhasil", "dihargai", "dianggap penting", "diikuti"],
    "aktivitas_negatif": ["diam", "menyendiri", "nggak usah ikut", "berhenti mencoba", "nonton saja"],
    "panjang": ["panjang", "berapi-api", "penuh janji", "sangat meyakinkan", "berjam-jam", "megah"],
    "kosong": ["kosong", "nggak jelas", "cuma janji", "tanpa solusi", "muter-muter", "tanpa isi"],
    "kosong_noun": ["janji", "wacana", "basa-basi", "formalitas", "omong kosong", "janji manis"],
    "julukan": ["si paling teliti", "si paling cepat", "si paling paham", "si profesional", "si rajin", "si paling siap"],
    "kasar": ["bego", "dodol", "goblok", "bodoh", "ngeselin", "usil", "konyol", "geblek", "bloon", "pekok"],
    "afeksi": ["aku kangen", "aku sayang", "aku nggak marah", "tetap temanku", "besok kita main lagi", "jangan lupa makan", "lucu", "nggak apa-apa", "kamu tetap sahabatku", "besok traktir aku ya", "aku nggak bisa marah lama", "kamu tetap yang terbaik", "jangan lupa istirahat"],
    "alasan_akrab": ["aku kangen", "kita sudah lama nggak ketemu", "tapi aku tetap sayang", "jangan lupa makan", "besok kita main lagi", "nggak usah dipikir", "aku cuma bercanda", "tapi aku tetap suka", "besok kita makan bareng", "jangan lupa balas chat", "aku cuma rindu", "tapi kamu tetap seru"],
    "bagian": ["pendahuluan", "analisis", "kesimpulan", "metodologi", "presentasi", "laporan", "desain", "kode", "abstrak", "diskusi", "lampiran", "slide"],
    "alasan_kritik": ["kurang data", "belum jelas", "terlalu panjang", "kurang contoh", "belum konsisten", "kurang sumber", "belum ada bukti", "terlalu umum", "kurang fokus"],
    "positif": ["idenya bagus", "strukturnya rapi", "datanya lengkap", "penjelasannya jelas", "usahanya terlihat", "desainnya menarik", "argumennya kuat", "contohnya relevan"],
    "positif_singkat": ["rapi", "jelas", "lengkap", "konsisten", "terstruktur", "menarik", "runtut", "padat", "fokus"],
    "perbaikan": ["bagian akhir perlu diringkas", "perlu menambah contoh", "kesimpulannya perlu diperjelas", "perlu data pendukung", "konsistensi istilah perlu dijaga", "perlu uji coba lagi"],
    "saran": ["tambahkan contoh konkret", "beri data terbaru", "ringkas bagian akhir", "perjelas bagian akhir", "jaga konsistensi istilah", "uji coba lagi", "tambah sumber", "perjelas alur"],
    "tujuan": ["lebih mudah dipahami", "argumennya lebih kuat", "tidak membingungkan", "lebih meyakinkan", "lebih mudah dinilai", "tidak melebar", "lebih fokus"],
    "perasaan": ["capek", "lapar", "ngantuk", "sedih", "kesal", "senang", "lelah", "bingung"],
    "sebab": ["kerjaan menumpuk", "hujan terus", "belum makan", "tidur kurang", "macet", "banyak tugas", "hp lowbat", "jadwal padat"],
    "cuaca": ["hujan", "panas", "mendung", "cerah"],
    "rencana": ["jalan-jalan", "nonton", "masak", "belajar", "olahraga"],
    "harapan": ["tidak hujan", "cuaca bagus", "sempat", "lancar", "tidak macet", "tidak hujan lagi"],
    "tempat": ["kantor pos", "bank", "supermarket", "klinik", "warung"],
    "aktivitas_netral": ["makan", "tidur", "kerja", "belajar", "olahraga", "bersih-bersih"],
    "tugas": ["presentasi", "tulisan", "desain", "kode", "ide", "penjelasan"],
    "pujian_singkat": ["bagus", "rapi", "jelas", "kreatif", "berguna", "keren"],
    "alasan_pujian": ["mudah dipahami", "enak dilihat", "detailnya kuat", "bikin semangat", "jelas sekali", "rapi sekali"],
    "hal": ["cara kamu menjelaskan", "ide kamu", "desainnya", "tulisannya", "caramu membantu"],
    "situasi": ["lagi serius", "lagi bingung", "lagi capek", "lagi marah", "presentasi"],
    "sifat": ["sabar", "ramah", "lucu", "tenang", "rajin", "perhatian"],
    "ajukan": ["presentasi meyakinkan", "bicara penuh istilah", "sok sibuk", "rapi di depan", "profesional"],
}

SEEDS: dict[str, list[str]] = {
    "sindiran": [
        "Wah, rajin sekali sampai lupa baca instruksi.",
        "Pintar sekali, salah dua kali pun tetap bangga.",
        "Katanya paling teliti, tapi detail penting kelewat.",
        "Hebat ya, cuma bisa nyalahin orang lain.",
        "Salut, kerjaan belum selesai tapi sudah minta dipuji.",
    ],
    "merendahkan": [
        "Orang seperti kamu memang cuma bikin lambat.",
        "Nggak usah ikut rapat, kamu nggak akan didengar.",
        "Kamu itu beban tim, bukan kontributor.",
        "Percuma minta tanggung jawab lebih, dasarnya nggak bisa diandalkan.",
        "Nggak ada yang butuh orang yang selalu beralasan seperti kamu.",
    ],
    "satir": [
        "Julukan si paling teliti memang pas, deadline lewat tapi tetap santai.",
        "Katanya paling profesional, tapi presentasinya belum siap.",
        "Gaya bicaranya meyakinkan, isinya kosong.",
        "Pantesan dijuluki si paling cepat, kerjaannya belum mulai.",
        "Ngaku paling paham, tapi pertanyaan dasar pun bingung.",
    ],
    "kasar_akrab": [
        "Dasar bego, tapi aku kangen.",
        "Goblok banget sih kamu, kita sudah lama nggak ketemu.",
        "Ngeselin, tapi besok kita main lagi ya.",
        "Dodol, jangan lupa makan.",
        "Bego ya, aku cuma bercanda.",
    ],
    "kritik": [
        "Bagian kesimpulan masih perlu diperjelas karena belum menjawab pertanyaan.",
        "Kritik membangun: idenya bagus, tetapi bagian akhir perlu diringkas.",
        "Presentasimu jelas, sayangnya belum ada data pendukung.",
        "Saran saya, tambahkan contoh agar lebih mudah dipahami.",
        "Laporannya rapi, hanya konsistensi istilah perlu dijaga.",
    ],
    "netral": [
        "Aku capek hari ini karena kerjaan menumpuk.",
        "Hari ini hujan, jadi rencana jalan-jalan batal.",
        "Antrean bank panjang, aku jadi lapar.",
        "Belum sempat makan karena banyak tugas.",
        "Aku sedang kerja, nanti balas ya.",
    ],
    "pujian": [
        "Presentasi kamu bagus, mudah dipahami.",
        "Aku suka cara kamu menjelaskan, sangat membantu.",
        "Desainnya rapi dan enak dilihat.",
        "Terima kasih, bantuanmu sangat berguna.",
        "Kamu lucu kalau lagi marah.",
    ],
}

TEMPLATES: dict[str, list[str]] = {
    "sindiran": [
        "Wah, {pujian} banget sampai {kegagalan}.",
        "{pujian}, tapi {kegagalan}.",
        "Hebat ya, {perilaku} saja {hasil}.",
        "Katanya {klaim}, tapi {kenyataan}.",
        "Sungguh {pujian}, {kegagalan} pun tetap dipuji.",
        "Nggak heran disebut {pujian}, {kegagalan} saja jadi masalah.",
        "Luar biasa, {aktivitas} sampai {kegagalan}.",
        "Wah {pujian}, {kegagalan} tapi tetap {sikap}.",
        "Pantas dipuji, {kegagalan} saja bisa jadi prestasi.",
        "Bagus banget, {kegagalan} tapi masih {sikap}.",
        "Memang {pujian}, {kegagalan} pun nggak bikin malu.",
        "Salut, {kegagalan} tapi {sikap}.",
        "Katanya {klaim}, {kenyataan} tapi tetap {sikap}.",
        "{pujian} sekali, {kegagalan} saja tidak dianggap masalah.",
        "Boleh juga, {pujian} tapi {kegagalan}.",
        "Keren, {aktivitas} tapi {kegagalan}.",
        "Kalau {pujian} diukur dari {kegagalan}, kamu juaranya.",
        "Nggak ada yang menyangkal {pujian}, {kegagalan} pun sudah biasa.",
        "Mantap, {kegagalan} tapi masih {sikap}.",
        "Kualitas {pujian}, hasilnya {kegagalan}.",
    ],
    "merendahkan": [
        "Orang seperti kamu memang {celaan}.",
        "{target} kayak kamu {celaan}.",
        "Nggak usah {aktivitas}, kamu nggak akan {hasil_merendahkan}.",
        "Kamu itu {celaan}, jadi jangan {aktivitas}.",
        "Percuma {aktivitas}, dasarnya {celaan}.",
        "Orang yang {celaan} seperti kamu nggak pantas {aktivitas}.",
        "Kamu ini {celaan}.",
        "Dari dulu kamu memang {celaan}.",
        "{target} seperti kamu lebih baik {aktivitas_negatif}.",
        "Nggak ada yang butuh orang yang {celaan} seperti kamu.",
        "Buat apa {aktivitas} kalau dasarnya {celaan}.",
        "Sayangnya, {target} seperti kamu memang {celaan}.",
        "Kalau {aktivitas}, kamu cuma {celaan}.",
        "Nggak perlu {aktivitas}, {target} seperti kamu memang {celaan}.",
    ],
    "satir": [
        "Julukan {julukan} memang pas, {kenyataan} tapi tetap {sikap}.",
        "Katanya {klaim}, tapi {kenyataan}.",
        "Gaya {ajukan}, hasilnya cuma {kosong_noun}.",
        "{klaim}, padahal {kenyataan}.",
        "Pantesan dijuluki {julukan}, {kenyataan} tapi tetap {sikap}.",
        "Ngaku {klaim}, tapi {kenyataan}.",
        "{julukan} memang cocok, {kenyataan} tapi tetap santai.",
        "Bicaranya {panjang}, isinya {kosong}.",
        "Katanya {klaim}, ternyata cuma {kosong_noun}.",
        "Semua {klaim}, tapi {kenyataan}.",
    ],
    "kasar_akrab": [
        "Dasar {kasar}, tapi {afeksi}.",
        "{kasar} banget sih kamu, {alasan_akrab}.",
        "Bego ya, {alasan_akrab}.",
        "Dasar {kasar}, {alasan_akrab}.",
        "Kamu {kasar}, tapi {afeksi}.",
        "Ngeselin, {alasan_akrab}.",
        "Dodol, {alasan_akrab}.",
        "{kasar} dikit boleh, {afeksi}.",
        "{kasar} sih kamu, {afeksi}.",
        "Kamu itu {kasar}, {alasan_akrab}.",
        "Dasar {kasar}, untung {afeksi}.",
        "Biar {kasar}, {afeksi}.",
        "Tetap {kasar}, tapi {afeksi}.",
        "Dodol banget, {afeksi}.",
    ],
    "kritik": [
        "Bagian {bagian} masih perlu diperbaiki karena {alasan_kritik}.",
        "Kritik membangun: {positif}, tetapi {perbaikan}.",
        "Secara umum {positif}, hanya {perbaikan}.",
        "{bagian} sudah {positif_singkat}, tetapi {perbaikan}.",
        "Saran saya, {perbaikan} agar {tujuan}.",
        "Presentasimu {positif_singkat}, sayangnya {perbaikan}.",
        "Isinya {positif_singkat}, tapi {perbaikan}.",
        "Menurut saya, {bagian} sebaiknya {saran} supaya {tujuan}.",
        "{bagian} sudah {positif_singkat}; {saran}.",
        "Saya sarankan {saran}; bagian {bagian} juga {positif_singkat}.",
        "Di balik {positif}, ada {bagian} yang perlu diperbaiki: {alasan_kritik}.",
        "Kalau boleh jujur, {bagian} {positif_singkat}, tetapi {perbaikan}.",
        "Catatan kecil: {saran} agar {tujuan}.",
        "Untuk {bagian}, coba {saran} dan pertimbangkan {tujuan}.",
        "Ada yang sudah {positif_singkat}, tetapi {bagian} masih lemah karena {alasan_kritik}.",
    ],
    "netral": [
        "Aku {perasaan} hari ini karena {sebab}.",
        "Hari ini {cuaca}, aku jadi {perasaan}.",
        "{perasaan} banget, {sebab}.",
        "Antrean {tempat} panjang, aku {perasaan}.",
        "Belum sempat {aktivitas_netral} karena {sebab}.",
        "Rencana {rencana} batal karena {sebab}.",
        "Aku sedang {aktivitas_netral}, nanti balas ya.",
        "Aku pengen {rencana}, tapi {sebab}.",
        "Hari ini {aktivitas_netral} saja, soalnya {sebab}.",
        "{tempat} ramai banget, aku jadi {perasaan}.",
        "Sudah {aktivitas_netral}, sekarang {perasaan}.",
        "Rencana {rencana} besok, semoga {harapan}.",
    ],
    "pujian": [
        "{tugas} kamu {pujian_singkat}, {alasan_pujian}.",
        "Aku suka {hal}, {alasan_pujian}.",
        "Kamu {sifat} kalau {situasi}.",
        "Terima kasih, {hal} sangat membantu.",
        "{tugas} tadi {pujian_singkat} sekali.",
        "Bercanda terus, {alasan_pujian}.",
        "Kamu lucu kalau {situasi}.",
    ],
}

PII_PATTERNS = [
    re.compile(r"https?://|www\.", re.IGNORECASE),
    re.compile(r"@\w+"),
    re.compile(r"\b08\d{7,11}\b"),
    re.compile(r"\b\d{10,}\b"),
]

EMOJIS_BY_CATEGORY = {
    "sindiran": ["😅", "🙃", "😌", "😬"],
    "merendahkan": ["🙃", "😌", "😬"],
    "satir": ["😅", "🙃", "😌"],
    "kasar_akrab": ["😅", "🙂", "😬"],
    "netral": ["🙂", "😌", "😅"],
    "pujian": ["🙂", "😌", "✨", "👍"],
}

CONTEXTS = [
    "Padahal sudah diingatkan berkali-kali.",
    "Dan itu bukan pertama kalinya.",
    "Padahal tetap saja dibela.",
    "Sudah sering terjadi seperti ini.",
    "Orang lain pun jadi ikut repot.",
    "Bahkan setelah ditegur, tetap sama.",
]
CONTEXT_CATEGORIES = {"sindiran", "merendahkan", "satir"}


def _clean(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return cleaned
    return cleaned[:1].upper() + cleaned[1:]


_DOUBLE_WORD_RE = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)
_BAD_FRAGMENTS = (
    "cuma nggak",
    "cuma tidak",
    "isinya usahanya",
    "di balik penjelasannya",
)


def _acceptable(text: str) -> bool:
    words = text.split()
    if not 3 <= len(words) <= 35:
        return False
    if _DOUBLE_WORD_RE.search(text):
        return False
    lower = text.lower()
    return not any(fragment in lower for fragment in _BAD_FRAGMENTS)


def generate_synthetic(
    counts: Mapping[str, tuple[int, int]] | None = None,
    seed: int = SEED,
    include_seeds: bool = True,
) -> pd.DataFrame:
    """Buat DataFrame sintetis deterministik sesuai jumlah per kategori."""
    counts = dict(DEFAULT_COUNTS if counts is None else counts)
    unknown = set(counts) - set(TEMPLATES)
    if unknown:
        raise ValueError(f"kategori tidak dikenal: {', '.join(sorted(unknown))}")

    normalized_counts: dict[str, tuple[int, int]] = {}
    for category, value in counts.items():
        if isinstance(value, tuple):
            label, target = value
        else:
            label, target = DEFAULT_COUNTS[category][0], int(value)
        normalized_counts[category] = (int(label), int(target))
    counts = normalized_counts

    rng = random.Random(seed)
    rows: list[dict[str, object]] = []
    seen: set[str] = set()

    for category, (label, target) in counts.items():
        made = 0
        if include_seeds:
            for seed_text in SEEDS[category]:
                if made >= target:
                    break
                text = _clean(seed_text)
                key = normalize_text(text)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        TEXT_COLUMN: text,
                        LABEL_COLUMN: label,
                        CATEGORY_COLUMN: category,
                        ORIGIN_COLUMN: "seed",
                    }
                )
                made += 1

        attempts = 0
        limit = max(10_000, target * 100)
        while made < target:
            attempts += 1
            if attempts > limit:
                raise RuntimeError(
                    f"kombinasi template tidak cukup untuk {category}: "
                    f"{made}/{target} baris unik"
                )
            pattern = rng.choice(TEMPLATES[category])
            values = {name: rng.choice(options) for name, options in SLOTS.items()}
            text = _clean(pattern.format(**values))
            if category in CONTEXT_CATEGORIES and rng.random() < 0.45:
                text = f"{text} {rng.choice(CONTEXTS)}"
            if category in EMOJIS_BY_CATEGORY and rng.random() < 0.55:
                text = f"{text} {rng.choice(EMOJIS_BY_CATEGORY[category])}"
            if not _acceptable(text):
                continue
            key = normalize_text(text)
            if not key or key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    TEXT_COLUMN: text,
                    LABEL_COLUMN: label,
                    CATEGORY_COLUMN: category,
                    ORIGIN_COLUMN: "template",
                }
            )
            made += 1

    rng.shuffle(rows)
    return pd.DataFrame(rows)


def check_synthetic(
    frame: pd.DataFrame,
    real_frames: Mapping[str, pd.DataFrame] | None = None,
    eval_frame: pd.DataFrame | None = None,
) -> dict[str, object]:
    """Validasi label, kategori, PII, duplikat, dan kebocoran ke split nyata."""
    errors: list[str] = []
    missing = {TEXT_COLUMN, LABEL_COLUMN, CATEGORY_COLUMN} - set(frame.columns)
    if missing:
        raise ValueError(f"kolom sintetis hilang: {', '.join(sorted(missing))}")

    if frame.empty:
        raise ValueError("data sintetis kosong")
    if frame[TEXT_COLUMN].isna().any():
        errors.append("ada teks kosong/NaN")
    if not set(frame[LABEL_COLUMN].unique()) <= {0, 1}:
        errors.append("label harus 0/1")
    if not set(frame[CATEGORY_COLUMN].unique()) <= set(DEFAULT_COUNTS):
        errors.append("ada kategori di luar daftar")

    for category, (expected_label, _) in DEFAULT_COUNTS.items():
        part = frame[frame[CATEGORY_COLUMN] == category]
        if not part.empty and set(part[LABEL_COLUMN].unique()) != {expected_label}:
            errors.append(f"label kategori {category} tidak konsisten")

    for pattern in PII_PATTERNS:
        hits = frame[TEXT_COLUMN].astype(str).str.contains(pattern, regex=True).sum()
        if hits:
            errors.append(f"ada {int(hits)} teks mengandung pola PII/URL/akun")

    normalized = frame[TEXT_COLUMN].astype(str).map(normalize_text)
    duplicates = int(normalized.duplicated().sum())
    if duplicates:
        errors.append(f"{duplicates} duplikat setelah normalisasi")

    overlaps: dict[str, int] = {}
    for name, real in (real_frames or {}).items():
        if TEXT_COLUMN not in real.columns:
            continue
        real_keys = set(real[TEXT_COLUMN].astype(str).map(normalize_text))
        overlap = len(set(normalized) & real_keys)
        overlaps[name] = overlap
        if overlap:
            errors.append(f"{overlap} teks sintetis overlap dengan {name}")

    if eval_frame is not None and TEXT_COLUMN in eval_frame.columns:
        eval_keys = set(eval_frame[TEXT_COLUMN].astype(str).map(normalize_text))
        overlap = len(set(normalized) & eval_keys)
        overlaps["eval"] = overlap
        if overlap:
            errors.append(f"{overlap} teks sintetis overlap dengan eval set")

    words = frame[TEXT_COLUMN].astype(str).str.split().str.len()
    if errors:
        raise ValueError("; ".join(errors))

    return {
        "rows": len(frame),
        "labels": frame[LABEL_COLUMN].value_counts().sort_index().to_dict(),
        "categories": frame[CATEGORY_COLUMN].value_counts().to_dict(),
        "origins": (
            frame[ORIGIN_COLUMN].value_counts().to_dict()
            if ORIGIN_COLUMN in frame.columns
            else {}
        ),
        "duplicates": duplicates,
        "overlaps": overlaps,
        "words": {
            "min": int(words.min()),
            "median": float(words.median()),
            "p95": float(words.quantile(0.95)),
            "max": int(words.max()),
        },
    }


def build_augmented_train(
    real_train: pd.DataFrame,
    synthetic: pd.DataFrame,
    real_val: pd.DataFrame,
    real_test: pd.DataFrame,
    eval_frame: pd.DataFrame | None = None,
    seed: int = SEED,
) -> pd.DataFrame:
    """Gabungkan train asli + sintetis tanpa menyentuh validation/test."""
    for name, frame in (("val", real_val), ("test", real_test)):
        overlap = set(real_train[TEXT_COLUMN].map(normalize_text)) & set(
            frame[TEXT_COLUMN].map(normalize_text)
        )
        if overlap:
            raise ValueError(f"train asli overlap dengan {name}: {len(overlap)} teks")

    real = real_train[[TEXT_COLUMN, LABEL_COLUMN]].copy()
    real["source"] = "real"
    syn = synthetic[[TEXT_COLUMN, LABEL_COLUMN]].copy()
    syn["source"] = "synthetic"

    combined = pd.concat([real, syn], ignore_index=True)
    combined["_key"] = combined[TEXT_COLUMN].map(normalize_text)
    combined = combined.drop_duplicates(subset="_key", keep="first")

    for name, frame in (("val", real_val), ("test", real_test)):
        keys = set(frame[TEXT_COLUMN].map(normalize_text))
        overlap = set(combined["_key"]) & keys
        if overlap:
            raise ValueError(f"train augmented overlap dengan {name}: {len(overlap)} teks")

    if eval_frame is not None and TEXT_COLUMN in eval_frame.columns:
        keys = set(eval_frame[TEXT_COLUMN].map(normalize_text))
        overlap = set(combined["_key"]) & keys
        if overlap:
            raise ValueError(f"train augmented overlap dengan eval: {len(overlap)} teks")

    combined = combined.drop(columns="_key")
    combined = combined.sample(frac=1, random_state=seed).reset_index(drop=True)
    return combined

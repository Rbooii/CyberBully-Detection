"""Normalisasi teks minimal agar sinyal sarkasme tidak hilang."""

import re
import unicodedata

URL_TOKEN = "<url>"
MENTION_TOKEN = "<user>"

_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_RE = re.compile(r"#(\w+)")
_WHITESPACE_RE = re.compile(r"\s+")
_ESCAPE_RUN_RE = re.compile(r"(?:\\x[0-9a-fA-F]{2})+")
_HEX_PAIR_RE = re.compile(r"\\x([0-9a-fA-F]{2})")


def repair_escaped_bytes(text: str) -> str:
    """Kembalikan escape ``\\xNN`` yang membentuk UTF-8 valid (artefak ekspor).

    Dataset re_dataset.csv menyimpan sebagian emoji sebagai teks literal
    ``\\xf0\\x9f...``. Run yang tidak membentuk UTF-8 valid dibiarkan apa adanya
    supaya tidak menebak-nebak.
    """
    if not isinstance(text, str):
        raise TypeError(f"teks harus str, bukan {type(text).__name__}")

    def _replace(match: re.Match[str]) -> str:
        raw = bytes(int(pair, 16) for pair in _HEX_PAIR_RE.findall(match.group(0)))
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return match.group(0)

    return _ESCAPE_RUN_RE.sub(_replace, text)


def normalize_text(text: str) -> str:
    """Normalisasi ringan: NFKC, casefold, samarkan URL/mention, rapikan spasi.

    Stopword, tanda baca, emoji, dan pengulangan huruf sengaja dipertahankan
    karena semuanya bisa membawa sinyal sarkasme atau penekanan.
    """
    if not isinstance(text, str):
        raise TypeError(f"teks harus str, bukan {type(text).__name__}")

    text = repair_escaped_bytes(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = text.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    text = _URL_RE.sub(f" {URL_TOKEN} ", text)
    text = _MENTION_RE.sub(f" {MENTION_TOKEN} ", text)
    text = _HASHTAG_RE.sub(r"\1", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()

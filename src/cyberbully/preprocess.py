"""Normalisasi teks minimal agar sinyal sarkasme tidak hilang."""

import re
import unicodedata

URL_TOKEN = "<url>"
MENTION_TOKEN = "<user>"

_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_RE = re.compile(r"#(\w+)")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Normalisasi ringan: NFKC, casefold, samarkan URL/mention, rapikan spasi.

    Stopword, tanda baca, emoji, dan pengulangan huruf sengaja dipertahankan
    karena semuanya bisa membawa sinyal sarkasme atau penekanan.
    """
    if not isinstance(text, str):
        raise TypeError(f"teks harus str, bukan {type(text).__name__}")

    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = _URL_RE.sub(f" {URL_TOKEN} ", text)
    text = _MENTION_RE.sub(f" {MENTION_TOKEN} ", text)
    text = _HASHTAG_RE.sub(r"\1", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()

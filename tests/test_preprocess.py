import pytest

from cyberbully.preprocess import (
    MENTION_TOKEN,
    URL_TOKEN,
    normalize_text,
    repair_escaped_bytes,
)


def test_keeps_emoji_and_punctuation() -> None:
    assert normalize_text("Dasar Bego!!! 😡") == "dasar bego!!! 😡"


def test_replaces_url_and_mention() -> None:
    result = normalize_text("Lihat https://example.com/x dan @budi ya")
    assert result == f"lihat {URL_TOKEN} dan {MENTION_TOKEN} ya"


def test_hashtag_keeps_word() -> None:
    assert normalize_text("#Goblok banget") == "goblok banget"


def test_collapses_whitespace_and_nfkc() -> None:
    assert normalize_text("  ｈａｌｏ \t dunia  ") == "halo dunia"


def test_idempotent() -> None:
    text = "  Dasar @user!!! https://a.co 😡  "
    once = normalize_text(text)
    assert normalize_text(once) == once


def test_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        normalize_text(None)  # type: ignore[arg-type]


def test_repairs_escaped_utf8_bytes() -> None:
    escaped = "dasar bodoh \\xf0\\x9f\\x98\\xa1"
    assert repair_escaped_bytes(escaped) == "dasar bodoh 😡"


def test_keeps_invalid_escape_run() -> None:
    assert repair_escaped_bytes("rusak \\x84") == "rusak \\x84"


def test_literal_newline_becomes_space() -> None:
    assert normalize_text("halo\\ndunia") == "halo dunia"


def test_normalize_repairs_escaped_emoji() -> None:
    assert normalize_text("DASAR BEGO!!! \\xf0\\x9f\\x98\\xa1") == "dasar bego!!! 😡"

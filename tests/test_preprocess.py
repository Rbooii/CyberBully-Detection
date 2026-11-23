import pytest

from cyberbully.preprocess import MENTION_TOKEN, URL_TOKEN, normalize_text


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

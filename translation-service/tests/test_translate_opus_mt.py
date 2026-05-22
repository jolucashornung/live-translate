import re

from app.main import TranslationResponse

CHINESE_CHAR_RE = re.compile(r"[一-鿿]")


def _post(client, text, source_lang, target_lang):
    return client.post(
        "/translate",
        json={"text": text, "source_lang": source_lang, "target_lang": target_lang},
    )


def test_en_to_zh_produces_chinese_characters(client):
    response = _post(client, "Hello, how are you?", "en", "zh")
    assert response.status_code == 200
    translated = response.json()["translated_text"]
    assert CHINESE_CHAR_RE.search(translated), f"No Chinese characters found in: {translated!r}"


def test_zh_to_en_produces_english_text(client):
    response = _post(client, "你好世界", "zh", "en")
    assert response.status_code == 200
    translated = response.json()["translated_text"].lower()
    assert any(word in translated for word in ("hello", "hi", "world", "greet")), (
        f"No recognizable English words found in: {translated!r}"
    )


def test_response_schema_matches_translation_response(client):
    response = _post(client, "Good morning.", "en", "zh")
    assert response.status_code == 200
    data = response.json()
    model = TranslationResponse(**data)
    assert model.source_lang == "en"
    assert model.target_lang == "zh"
    assert isinstance(model.translated_text, str)


def test_longer_paragraph_translates_without_error(client):
    paragraph = (
        "The quick brown fox jumps over the lazy dog. "
        "It was a bright cold day in April, and the clocks were striking thirteen. "
        "All happy families are alike; each unhappy family is unhappy in its own way."
    )
    response = _post(client, paragraph, "en", "zh")
    assert response.status_code == 200
    data = response.json()
    assert len(data["translated_text"]) > 0
    assert CHINESE_CHAR_RE.search(data["translated_text"])

from app.nlp.analyzer import analyze_text
from app.nlp.dictionary_classifier import get_dictionary_classifier
from app.nlp.preprocess import preprocess, PreprocessConfig
from app.nlp.tokenizer import tokenize


def test_english_only():
    result = analyze_text("Please send the report tomorrow.", model_override="dictionary")
    assert result["summary"]["english"] >= 3
    assert result["code_switching"]["status"] in {"NO", "INSUFFICIENT_EVIDENCE"}


def test_roman_urdu_only():
    result = analyze_text("Aaj mausam bohot acha hai.", model_override="dictionary")
    assert result["summary"]["roman_urdu"] >= 3
    assert "English" not in result["code_switching"]["detected_languages"] or result["summary"]["english"] == 0


def test_mixed_language_example():
    result = analyze_text(
        "Main university mein admission apply kar raha hoon.",
        model_override="dictionary",
    )
    labels = {t["token"].lower(): t["label"] for t in result["tokens"] if t["kind"] == "word"}
    assert labels.get("main") == "URDU_ROMAN"
    assert labels.get("university") == "ENGLISH"
    assert labels.get("mein") == "URDU_ROMAN"
    assert labels.get("admission") == "ENGLISH"
    assert labels.get("apply") == "ENGLISH"
    assert labels.get("kar") == "URDU_ROMAN"
    assert result["code_switching"]["status"] == "YES"
    assert result["summary"]["roman_urdu"] >= 4
    assert result["summary"]["english"] >= 3


def test_empty_text():
    result = analyze_text("   ", model_override="dictionary")
    assert result["summary"]["total_words"] == 0
    assert result["code_switching"]["status"] == "INSUFFICIENT_EVIDENCE"


def test_punctuation_numbers_url_emoji():
    result = analyze_text("Hello 123!!! https://example.com 😀", model_override="dictionary")
    kinds = {t["kind"] for t in result["tokens"]}
    assert "punct" in kinds or any(t["label"] == "OTHER" for t in result["tokens"])
    assert "number" in kinds or "url" in kinds or "emoji" in kinds


def test_ambiguous_not_forced():
    clf = get_dictionary_classifier()
    toks = tokenize("to so me")
    preds = clf.predict_tokens(toks)
    assert any(p.label.value == "AMBIGUOUS" for p in preds)


def test_preprocess_normalization():
    cfg = PreprocessConfig(roman_urdu_normalize=True, lowercase=True)
    result = preprocess("Achha hai nahin", cfg)
    assert "acha" in result.normalized or "nahi" in result.normalized


def test_long_paragraph():
    text = "Main university mein admission apply kar raha hoon. " * 20
    result = analyze_text(text, model_override="dictionary")
    assert result["summary"]["total_words"] > 50
    assert len(result["sentences"]) >= 1

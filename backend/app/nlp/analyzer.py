from __future__ import annotations

import re
from typing import Any

from app.nlp.codeswitch import detect_code_switching, summarize_predictions
from app.nlp.dictionary_classifier import DictionaryClassifier, get_dictionary_classifier
from app.nlp.ml_inference import try_predict_with_active_model
from app.nlp.preprocess import PreprocessConfig, preprocess
from app.nlp.tokenizer import tokenize


def _sentence_spans(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def analyze_text(
    text: str,
    *,
    use_preprocessing: bool = True,
    preprocess_config: PreprocessConfig | None = None,
    model_override: str | None = None,
    db_session: Any | None = None,
) -> dict:
    if text is None or not str(text).strip():
        return {
            "text": text or "",
            "tokens": [],
            "summary": {
                "total_words": 0,
                "roman_urdu": 0,
                "english": 0,
                "ambiguous": 0,
                "unknown": 0,
                "other_tokens": 0,
                "urdu_percentage": 0.0,
                "english_percentage": 0.0,
                "most_frequent_english": [],
                "most_frequent_urdu": [],
                "confidence_distribution": {"high": 0, "medium": 0, "low": 0, "none": 0},
                "ambiguous_words": [],
                "mean_confidence": None,
            },
            "code_switching": {
                "status": "INSUFFICIENT_EVIDENCE",
                "sentence_label": "INSUFFICIENT_EVIDENCE",
                "detected_languages": [],
                "transitions": {"urdu_to_english": 0, "english_to_urdu": 0, "total": 0},
                "reliable_urdu_tokens": 0,
                "reliable_english_tokens": 0,
            },
            "preprocessing": None,
            "model": {
                "name": "dictionary-baseline",
                "version": DictionaryClassifier.MODEL_VERSION,
                "source": "fallback",
            },
            "sentences": [],
            "char_count": 0,
            "word_count": 0,
        }

    cfg = preprocess_config or PreprocessConfig(roman_urdu_normalize=use_preprocessing)
    if not use_preprocessing:
        cfg = PreprocessConfig(
            unicode_normalize=True,
            clean_text=True,
            whitespace_normalize=True,
            lowercase=False,
            collapse_repeated_chars=False,
            roman_urdu_normalize=False,
        )

    prep = preprocess(text, cfg)
    tokens = prep.tokens if use_preprocessing else tokenize(text)

    ml_preds = None
    model_meta = {
        "name": "dictionary-baseline",
        "version": DictionaryClassifier.MODEL_VERSION,
        "source": "dictionary",
    }
    if model_override != "dictionary":
        ml_preds, model_meta_ml = try_predict_with_active_model(
            tokens, prep.token_texts if use_preprocessing else [t.text for t in tokens], db_session
        )
        if ml_preds is not None:
            preds = ml_preds
            model_meta = model_meta_ml
        else:
            clf = get_dictionary_classifier()
            preds = clf.predict_tokens(tokens, prep.token_texts if use_preprocessing else None)
            model_meta["source"] = "dictionary-fallback"
    else:
        clf = get_dictionary_classifier()
        preds = clf.predict_tokens(tokens, prep.token_texts if use_preprocessing else None)

    summary = summarize_predictions(preds)
    cs = detect_code_switching(preds)

    # Sentence-level breakdown
    sentences = []
    for sent in _sentence_spans(text):
        s_prep = preprocess(sent, cfg)
        s_tokens = s_prep.tokens
        if model_meta.get("source", "").startswith("ml"):
            s_preds, _meta = try_predict_with_active_model(
                s_tokens, s_prep.token_texts, db_session
            )
            if s_preds is None:
                s_preds = get_dictionary_classifier().predict_tokens(s_tokens, s_prep.token_texts)
        else:
            s_preds = get_dictionary_classifier().predict_tokens(s_tokens, s_prep.token_texts)
        sentences.append(
            {
                "text": sent,
                "summary": summarize_predictions(s_preds),
                "code_switching": detect_code_switching(s_preds),
                "tokens": [
                    {
                        "token": p.token,
                        "label": p.label.value,
                        "confidence": p.confidence,
                        "position": p.position,
                        "model_version": p.model_version,
                        "alternative": p.alternative,
                        "kind": p.kind,
                    }
                    for p in s_preds
                ],
            }
        )

    word_count = summary["total_words"]
    return {
        "text": text,
        "tokens": [
            {
                "token": p.token,
                "label": p.label.value,
                "confidence": p.confidence,
                "position": p.position,
                "model_version": p.model_version,
                "alternative": p.alternative,
                "kind": p.kind,
                "start": tokens[i].start if i < len(tokens) else None,
                "end": tokens[i].end if i < len(tokens) else None,
            }
            for i, p in enumerate(preds)
        ],
        "summary": summary,
        "code_switching": cs,
        "preprocessing": {
            "original": prep.original,
            "cleaned": prep.cleaned,
            "normalized": prep.normalized,
            "tokenized": prep.token_texts,
            "config": prep.config,
            "enabled": use_preprocessing,
        },
        "model": model_meta,
        "sentences": sentences,
        "char_count": len(text),
        "word_count": word_count,
    }


def analyze_batch(texts: list[str], **kwargs) -> list[dict]:
    return [analyze_text(t, **kwargs) for t in texts]

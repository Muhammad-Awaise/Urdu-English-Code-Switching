from __future__ import annotations

from collections import Counter

from app.core.runtime_settings import cs_min_confidence, cs_min_tokens_per_language
from app.nlp.dictionary_classifier import Prediction
from app.nlp.labels import CodeSwitchStatus, SentenceLabel, TokenLabel


LANG_LABELS = {TokenLabel.URDU_ROMAN, TokenLabel.ENGLISH}


def language_sequence(preds: list[Prediction]) -> list[str]:
    seq: list[str] = []
    min_conf = cs_min_confidence()
    for p in preds:
        if p.label in LANG_LABELS:
            if p.confidence is not None and p.confidence < min_conf:
                continue
            seq.append(p.label.value)
    return seq


def count_transitions(seq: list[str]) -> dict[str, int]:
    urdu_to_eng = 0
    eng_to_urdu = 0
    for a, b in zip(seq, seq[1:]):
        if a == TokenLabel.URDU_ROMAN.value and b == TokenLabel.ENGLISH.value:
            urdu_to_eng += 1
        elif a == TokenLabel.ENGLISH.value and b == TokenLabel.URDU_ROMAN.value:
            eng_to_urdu += 1
    return {
        "urdu_to_english": urdu_to_eng,
        "english_to_urdu": eng_to_urdu,
        "total": urdu_to_eng + eng_to_urdu,
    }


def detect_code_switching(preds: list[Prediction]) -> dict:
    """
    Policy:
    - Count only URDU_ROMAN / ENGLISH tokens meeting min confidence.
    - YES if both languages appear with >= cs_min_tokens_per_language each.
    - NO if exactly one language is reliably present.
    - INSUFFICIENT_EVIDENCE otherwise (no reliable language tokens, or only ambiguous/unknown).
    """
    min_conf = cs_min_confidence()
    conf_urdu = [
        p
        for p in preds
        if p.label == TokenLabel.URDU_ROMAN
        and (p.confidence is None or p.confidence >= min_conf)
    ]
    conf_eng = [
        p
        for p in preds
        if p.label == TokenLabel.ENGLISH
        and (p.confidence is None or p.confidence >= min_conf)
    ]
    n_u = len(conf_urdu)
    n_e = len(conf_eng)
    min_n = cs_min_tokens_per_language()

    if n_u >= min_n and n_e >= min_n:
        status = CodeSwitchStatus.YES
        sentence_label = SentenceLabel.CODE_SWITCHED
    elif n_u >= min_n and n_e == 0:
        status = CodeSwitchStatus.NO
        sentence_label = SentenceLabel.URDU_ONLY
    elif n_e >= min_n and n_u == 0:
        status = CodeSwitchStatus.NO
        sentence_label = SentenceLabel.ENGLISH_ONLY
    else:
        status = CodeSwitchStatus.INSUFFICIENT_EVIDENCE
        sentence_label = SentenceLabel.INSUFFICIENT_EVIDENCE

    detected = []
    if n_u >= min_n:
        detected.append("Urdu")
    if n_e >= min_n:
        detected.append("English")

    seq = language_sequence(preds)
    transitions = count_transitions(seq)

    return {
        "status": status.value,
        "sentence_label": sentence_label.value,
        "detected_languages": detected,
        "transitions": transitions,
        "reliable_urdu_tokens": n_u,
        "reliable_english_tokens": n_e,
    }


def summarize_predictions(preds: list[Prediction]) -> dict:
    word_preds = [p for p in preds if p.kind == "word"]
    counts = Counter(p.label.value for p in word_preds)
    total = len(word_preds) or 1
    urdu = counts.get(TokenLabel.URDU_ROMAN.value, 0)
    eng = counts.get(TokenLabel.ENGLISH.value, 0)
    amb = counts.get(TokenLabel.AMBIGUOUS.value, 0)
    unk = counts.get(TokenLabel.UNKNOWN.value, 0)

    eng_freq = Counter(p.token.lower() for p in word_preds if p.label == TokenLabel.ENGLISH)
    urdu_freq = Counter(p.token.lower() for p in word_preds if p.label == TokenLabel.URDU_ROMAN)

    confidences = [p.confidence for p in word_preds if p.confidence is not None]
    conf_buckets = {"high": 0, "medium": 0, "low": 0, "none": 0}
    for c in [p.confidence for p in word_preds]:
        if c is None:
            conf_buckets["none"] += 1
        elif c >= 0.8:
            conf_buckets["high"] += 1
        elif c >= 0.55:
            conf_buckets["medium"] += 1
        else:
            conf_buckets["low"] += 1

    return {
        "total_words": len(word_preds),
        "roman_urdu": urdu,
        "english": eng,
        "ambiguous": amb,
        "unknown": unk,
        "other_tokens": sum(1 for p in preds if p.kind != "word"),
        "urdu_percentage": round(100.0 * urdu / total, 2),
        "english_percentage": round(100.0 * eng / total, 2),
        "most_frequent_english": eng_freq.most_common(10),
        "most_frequent_urdu": urdu_freq.most_common(10),
        "confidence_distribution": conf_buckets,
        "ambiguous_words": [
            {"token": p.token, "position": p.position, "alternative": p.alternative}
            for p in word_preds
            if p.label == TokenLabel.AMBIGUOUS
        ],
        "mean_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
    }

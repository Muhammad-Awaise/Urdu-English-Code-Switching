from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from app.nlp.tokenizer import Token, tokenize


DEFAULT_ROMAN_URDU_NORM = {
    "achha": "acha",
    "achaa": "acha",
    "hay": "hai",
    "he": "hai",  # careful: English "he" handled via ambiguous set elsewhere
    "nahin": "nahi",
    "nahiin": "nahi",
    "naheen": "nahi",
    "kia": "kya",
    "mujy": "mujhe",
    "mujhay": "mujhe",
    "mujhay": "mujhe",
    "apko": "aapko",
    "ap": "aap",
    "kriye": "kariye",
    "karo": "karo",
    "kr": "kar",
    "rahay": "rahe",
    "raha": "raha",
    "rha": "raha",
    "rhe": "rahe",
    "hn": "hain",
    "hun": "hoon",
    "houn": "hoon",
    "mein": "main",  # orthographic variant; researcher-configurable
    "may": "main",
}


@dataclass
class PreprocessConfig:
    unicode_normalize: bool = True
    clean_text: bool = True
    whitespace_normalize: bool = True
    lowercase: bool = True
    collapse_repeated_chars: bool = True
    roman_urdu_normalize: bool = True
    detect_urls: bool = True
    handle_emoji: bool = True
    custom_norm_map: dict[str, str] = field(default_factory=dict)
    # Do not force English "he"/"may" through Urdu map when disabled
    safe_norm_only: bool = True


SAFE_NORM_BLOCKLIST = {"he", "may", "so", "to", "or", "no", "in", "on", "us", "me", "am", "is", "are"}


@dataclass
class PreprocessResult:
    original: str
    cleaned: str
    normalized: str
    tokens: list[Token]
    token_texts: list[str]
    config: dict


def _collapse_repeats(text: str) -> str:
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def clean_text(text: str, cfg: PreprocessConfig) -> str:
    out = text
    if cfg.unicode_normalize:
        out = unicodedata.normalize("NFKC", out)
    if cfg.clean_text:
        out = out.replace("\u200f", "").replace("\u200e", "")
        out = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", out)
    if cfg.whitespace_normalize:
        out = re.sub(r"\s+", " ", out).strip()
    return out


def normalize_token(token: str, cfg: PreprocessConfig) -> str:
    t = token
    if cfg.lowercase:
        t = t.lower()
    if cfg.collapse_repeated_chars:
        t = _collapse_repeats(t)
    if cfg.roman_urdu_normalize:
        mapping = {**DEFAULT_ROMAN_URDU_NORM, **cfg.custom_norm_map}
        key = t.lower()
        if cfg.safe_norm_only and key in SAFE_NORM_BLOCKLIST:
            return t
        if key in mapping:
            t = mapping[key]
    return t


def preprocess(text: str, cfg: PreprocessConfig | None = None) -> PreprocessResult:
    cfg = cfg or PreprocessConfig()
    cleaned = clean_text(text, cfg)
    working = cleaned
    if cfg.lowercase:
        # Keep original casing in tokens from cleaned; apply lower later per token
        pass
    tokens = tokenize(working)
    norm_tokens = []
    for tok in tokens:
        if tok.kind == "word":
            norm_tokens.append(normalize_token(tok.text, cfg))
        else:
            norm_tokens.append(tok.text)
    normalized = " ".join(norm_tokens)
    return PreprocessResult(
        original=text,
        cleaned=cleaned,
        normalized=normalized,
        tokens=tokens,
        token_texts=norm_tokens,
        config=cfg.__dict__ | {"custom_norm_map": dict(cfg.custom_norm_map)},
    )

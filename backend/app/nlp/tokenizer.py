from __future__ import annotations

import re
from dataclasses import dataclass

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@[A-Za-z0-9_]+")
HASHTAG_RE = re.compile(r"#[\w]+", re.UNICODE)
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
NUMBER_RE = re.compile(r"^\d+([.,]\d+)?$")
PUNCT_RE = re.compile(r"^[^\w]+$", re.UNICODE)

# Keep Latin words, numbers, punctuation, URLs as separate tokens
TOKEN_RE = re.compile(
    r"https?://\S+|www\.\S+|@[A-Za-z0-9_]+|#[\w]+|"
    r"[\w']+|[^\w\s]",
    re.UNICODE,
)


@dataclass
class Token:
    text: str
    position: int
    start: int
    end: int
    kind: str  # word | punct | number | url | mention | hashtag | emoji | other


def classify_token_kind(text: str) -> str:
    if URL_RE.fullmatch(text):
        return "url"
    if MENTION_RE.fullmatch(text):
        return "mention"
    if HASHTAG_RE.fullmatch(text):
        return "hashtag"
    if EMOJI_RE.fullmatch(text):
        return "emoji"
    if NUMBER_RE.fullmatch(text):
        return "number"
    if PUNCT_RE.fullmatch(text):
        return "punct"
    if re.search(r"[A-Za-z]", text):
        return "word"
    return "other"


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    for match in TOKEN_RE.finditer(text):
        raw = match.group(0)
        kind = classify_token_kind(raw)
        tokens.append(
            Token(
                text=raw,
                position=pos,
                start=match.start(),
                end=match.end(),
                kind=kind,
            )
        )
        pos += 1
    return tokens

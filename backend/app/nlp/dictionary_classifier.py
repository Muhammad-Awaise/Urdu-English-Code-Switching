from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.nlp.labels import TokenLabel
from app.nlp.preprocess import PreprocessConfig, normalize_token
from app.nlp.tokenizer import Token


@dataclass
class Prediction:
    token: str
    label: TokenLabel
    confidence: float | None
    position: int
    model_version: str
    alternative: str | None = None
    kind: str = "word"


class DictionaryClassifier:
    """Local lexicon baseline for word-level language ID."""

    MODEL_VERSION = "dictionary-baseline-v1"

    def __init__(
        self,
        urdu_path: Path | None = None,
        english_path: Path | None = None,
        ambiguous_path: Path | None = None,
    ) -> None:
        lex = settings.lexicon_dir
        self.urdu = self._load_set(urdu_path or lex / "roman_urdu.txt")
        self.english = self._load_set(english_path or lex / "english_common.txt")
        self.ambiguous = self._load_set(ambiguous_path or lex / "ambiguous.txt")
        self.preprocess_cfg = PreprocessConfig(roman_urdu_normalize=True, safe_norm_only=True)

    @staticmethod
    def _load_set(path: Path) -> set[str]:
        if not path.exists():
            return set()
        words: set[str] = set()
        text = path.read_text(encoding="utf-8-sig")
        for line in text.splitlines():
            w = line.strip().lower()
            if w and not w.startswith("#"):
                words.add(w)
        return words

    def predict_token(self, token: Token, normalized: str | None = None) -> Prediction:
        if token.kind != "word":
            return Prediction(
                token=token.text,
                label=TokenLabel.OTHER,
                confidence=1.0,
                position=token.position,
                model_version=self.MODEL_VERSION,
                kind=token.kind,
            )

        norm = (normalized or normalize_token(token.text, self.preprocess_cfg)).lower()
        raw = token.text.lower()

        in_urdu = norm in self.urdu or raw in self.urdu
        in_eng = norm in self.english or raw in self.english
        in_amb = norm in self.ambiguous or raw in self.ambiguous

        if in_amb or (in_urdu and in_eng):
            return Prediction(
                token=token.text,
                label=TokenLabel.AMBIGUOUS,
                confidence=0.5,
                position=token.position,
                model_version=self.MODEL_VERSION,
                alternative="URDU_ROMAN" if in_urdu else ("ENGLISH" if in_eng else None),
                kind=token.kind,
            )
        if in_urdu:
            return Prediction(
                token=token.text,
                label=TokenLabel.URDU_ROMAN,
                confidence=0.9,
                position=token.position,
                model_version=self.MODEL_VERSION,
                alternative="ENGLISH" if in_eng else None,
                kind=token.kind,
            )
        if in_eng:
            return Prediction(
                token=token.text,
                label=TokenLabel.ENGLISH,
                confidence=0.9,
                position=token.position,
                model_version=self.MODEL_VERSION,
                kind=token.kind,
            )
        return Prediction(
            token=token.text,
            label=TokenLabel.UNKNOWN,
            confidence=0.4,
            position=token.position,
            model_version=self.MODEL_VERSION,
            kind=token.kind,
        )

    def predict_tokens(self, tokens: list[Token], normalized_texts: list[str] | None = None) -> list[Prediction]:
        out: list[Prediction] = []
        for i, tok in enumerate(tokens):
            norm = normalized_texts[i] if normalized_texts and i < len(normalized_texts) else None
            out.append(self.predict_token(tok, norm))
        return out


_classifier: DictionaryClassifier | None = None


def get_dictionary_classifier() -> DictionaryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DictionaryClassifier()
    return _classifier

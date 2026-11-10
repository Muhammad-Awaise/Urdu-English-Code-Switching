# Annotation Guide

1. Tokenize consistently with the app tokenizer when possible.
2. Label Roman Urdu function/content words as `URDU_ROMAN`.
3. Label English words as `ENGLISH`.
4. If a token is plausible in both languages, use `AMBIGUOUS` — do not force a side.
5. Use `UNKNOWN` when unsure.
6. Punctuation, numbers, URLs, mentions, emojis → `OTHER`.
7. Mark uncertain tokens and add notes for review.
8. Prefer quality over speed; keep annotator identity if multiple people contribute.

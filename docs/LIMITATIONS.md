# Limitations

- Dictionary coverage is incomplete; many valid tokens will be `UNKNOWN`.
- Token classifiers ignore wider syntactic context.
- Roman Urdu spelling variation is open-ended; normalization maps are partial and configurable, not authoritative.
- Seeded sample dataset is too small for research claims.
- Ambiguous Latin-script tokens are inherently difficult.
- Linear models may underperform on rare morphological patterns.
- Optional deep models are not enabled by default and must not auto-download large weights.

# Preprocessing

Pipeline steps (configurable):

1. Unicode normalization (NFKC)
2. Control-character cleaning
3. Whitespace normalization
4. Tokenization
5. Optional lowercase
6. Repeated-character collapse (`booooot` → `boot`)
7. Optional Roman Urdu spelling map (`achha`→`acha`, `nahin`→`nahi`, …)
8. URL / emoji / mention detection via tokenizer kinds

Safe mode blocks mapping English-sensitive tokens like `he` / `may` through Urdu maps.

Compare predictions with preprocessing enabled vs disabled in the Preprocessing Lab and Analyzer toggle.

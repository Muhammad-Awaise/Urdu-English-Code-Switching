# Dataset Guide

## Supported formats

CSV, Excel, JSON, JSONL, and manual sentence entry.

Recommended JSON record:

```json
{
  "sentence_id": "001",
  "text": "Main university mein admission apply kar raha hoon.",
  "annotations": [
    {"token": "Main", "label": "URDU_ROMAN"},
    {"token": "university", "label": "ENGLISH"}
  ]
}
```

## Labels

`URDU_ROMAN`, `ENGLISH`, `AMBIGUOUS`, `UNKNOWN`, `OTHER`

## Seeded sample

`sample_code_switching` is a tiny illustrative set for pipeline testing only.

## External data policy

Only import datasets after verifying:

1. License allows local research use  
2. Word-level labels exist (or you will annotate)  
3. Roman Urdu is actually present  

Do not scrape private conversations or paid corpora.

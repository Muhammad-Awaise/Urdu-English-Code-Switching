from fastapi import APIRouter

from app.api.schemas import PreprocessRequest
from app.nlp.preprocess import PreprocessConfig, preprocess

router = APIRouter()


@router.post("/preprocess")
def run_preprocess(payload: PreprocessRequest):
    cfg = PreprocessConfig(
        unicode_normalize=payload.unicode_normalize,
        clean_text=payload.clean_text,
        whitespace_normalize=payload.whitespace_normalize,
        lowercase=payload.lowercase,
        collapse_repeated_chars=payload.collapse_repeated_chars,
        roman_urdu_normalize=payload.roman_urdu_normalize,
        custom_norm_map=payload.custom_norm_map,
    )
    result = preprocess(payload.text, cfg)
    disabled = preprocess(
        payload.text,
        PreprocessConfig(
            unicode_normalize=True,
            clean_text=True,
            whitespace_normalize=True,
            lowercase=False,
            collapse_repeated_chars=False,
            roman_urdu_normalize=False,
        ),
    )
    return {
        "with_preprocessing": {
            "original": result.original,
            "cleaned": result.cleaned,
            "normalized": result.normalized,
            "tokenized": result.token_texts,
            "config": result.config,
        },
        "without_roman_normalization": {
            "original": disabled.original,
            "cleaned": disabled.cleaned,
            "normalized": disabled.normalized,
            "tokenized": disabled.token_texts,
            "config": disabled.config,
        },
    }

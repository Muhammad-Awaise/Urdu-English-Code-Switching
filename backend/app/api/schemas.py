from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str
    use_preprocessing: bool = True
    model_override: str | None = None


class BatchAnalyzeRequest(BaseModel):
    texts: list[str]
    use_preprocessing: bool = True


class PreprocessRequest(BaseModel):
    text: str
    unicode_normalize: bool = True
    clean_text: bool = True
    whitespace_normalize: bool = True
    lowercase: bool = True
    collapse_repeated_chars: bool = True
    roman_urdu_normalize: bool = True
    custom_norm_map: dict[str, str] = Field(default_factory=dict)


class DatasetCreate(BaseModel):
    name: str
    description: str | None = None
    source: str | None = None
    license_note: str | None = None


class AnnotationItem(BaseModel):
    token: str
    label: str
    position: int | None = None
    uncertain: bool = False
    note: str | None = None
    annotator: str | None = None


class SentenceCreate(BaseModel):
    text: str
    sentence_id: str | None = None
    annotations: list[AnnotationItem] = Field(default_factory=list)
    notes: str | None = None
    annotator: str | None = None


class AnnotationUpdate(BaseModel):
    label: str | None = None
    uncertain: bool | None = None
    note: str | None = None
    annotator: str | None = None


class SplitRequest(BaseModel):
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    seed: int = 42


class CleanRequest(BaseModel):
    remove_empty: bool = True
    remove_duplicates: bool = False


class TrainRequest(BaseModel):
    dataset_version_id: int
    model_type: str = "logreg"
    word_ngram_range: list[int] = Field(default_factory=lambda: [1, 1])
    char_ngram_range: list[int] = Field(default_factory=lambda: [2, 5])
    C: float = 1.0
    class_weight: str | None = "balanced"
    random_seed: int = 42
    use_char: bool = True
    use_word: bool = True
    max_features: int = 50000
    hypothesis: str | None = None
    research_question: str | None = None
    confirm_large_run: bool = False


class NoteCreate(BaseModel):
    title: str
    category: str
    content: str
    tags: list[str] | None = None
    linked_experiment_id: str | None = None
    linked_model_id: int | None = None
    linked_dataset_id: int | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class PaperCreate(BaseModel):
    title: str
    authors: str | None = None
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    free_fulltext_url: str | None = None
    research_objective: str | None = None
    dataset: str | None = None
    methodology: str | None = None
    model: str | None = None
    reported_results: str | None = None
    findings: str | None = None
    limitations: str | None = None
    relevance: str | None = None


class FindingCreate(BaseModel):
    title: str
    content: str
    is_hypothesis: bool = False
    linked_experiment_id: str | None = None


class ReportRequest(BaseModel):
    report_type: str = "complete"
    format: str = "markdown"


class SettingsUpdate(BaseModel):
    values: dict[str, Any]

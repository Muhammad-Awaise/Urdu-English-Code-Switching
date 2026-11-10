from enum import Enum


class TokenLabel(str, Enum):
    URDU_ROMAN = "URDU_ROMAN"
    ENGLISH = "ENGLISH"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"
    OTHER = "OTHER"


class CodeSwitchStatus(str, Enum):
    YES = "YES"
    NO = "NO"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class SentenceLabel(str, Enum):
    CODE_SWITCHED = "CODE_SWITCHED"
    URDU_ONLY = "URDU_ONLY"
    ENGLISH_ONLY = "ENGLISH_ONLY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

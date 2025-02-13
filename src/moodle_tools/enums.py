from enum import StrEnum, auto


class ShuffleAnswersEnum(StrEnum):
    SHUFFLE = auto()
    IN_ORDER = auto()
    LEXICOGRAPHICAL = auto()
    NONE = auto()

    @classmethod
    def from_str(cls, value: str) -> "ShuffleAnswersEnum":
        return cls[value.upper()] if value else cls.NONE


class ClozeTypeEnum(StrEnum):
    SHORTANSWER = "SHORTANSWER"
    NUMERICAL = "NUMERICAL"
    MULTICHOICE = "MULTICHOICE"
    MULTIRESPONSE = "MULTIRESPONSE"

    @classmethod
    def from_str(cls, value: str) -> "ClozeTypeEnum":
        return cls[value.upper()]


class DisplayFormatEnum(StrEnum):
    DROPDOWN = auto()
    HORIZONTAL = auto()
    VERTICAL = auto()
    NONE = auto()

    @classmethod
    def from_str(cls, value: str) -> "DisplayFormatEnum":
        return cls[value.upper()] if value else cls.NONE

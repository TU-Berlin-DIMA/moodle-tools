from enum import IntEnum, StrEnum, auto


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


class EditorType(StrEnum):
    NOINLINE = auto()
    PLAIN = auto()
    MONOSPACED = auto()
    EDITOR = auto()
    EDITORFILEPICKER = auto()

    @classmethod
    def from_str(cls, value: str) -> "EditorType":
        return cls[value.upper()] if value else cls.EDITORFILEPICKER


class PredefinedFileTypes(StrEnum):
    ARCHIVE = auto()
    AUDIO = auto()
    HTML_AUDIO = auto()
    WEB_AUDIO = auto()
    DOCUMENT = auto()
    HTML_TRACK = auto()
    IMAGE = auto()
    OPTIMISED_IMAGE = auto()
    WEB_IMAGE = auto()
    PRESENTATION = auto()
    SOURCECODE = auto()
    SPREADSHEET = auto()
    MEDIA_SOURCE = auto()
    VIDEO = auto()
    HTML_VIDEO = auto()
    WEB_VIDEO = auto()
    WEB_FILE = auto()
    NONE = auto()

    @classmethod
    def from_str(cls, value: str) -> "PredefinedFileTypes":
        return cls[value.upper()] if value else cls.NONE


class EnumerationStyle(StrEnum):
    NONE = "none"
    ALPHABET_LOWER = "abc"
    ALPAHBET_UPPER = "ABCD"
    ROMAN_LOWER = "iii"
    ROMAN_UPPER = "IIII"
    NUMBERS = "123"

    @classmethod
    def from_str(cls, value: str) -> "EnumerationStyle":
        return cls[value.upper()] if value else cls.ALPHABET_LOWER


class SelectType(IntEnum):
    ALL_ELEMENTS = 2
    RANDOM_ELEMENTS = 1
    CONNECTED_ELEMENTS = 2

    @classmethod
    def from_str(cls, value: str) -> "SelectType":
        return cls[value.upper()] if value else cls.ALL_ELEMENTS


class GradingType(IntEnum):
    ALL_OR_NOTHING = -1
    ABSOLUTE_POSITION = 0
    RELATIVE_POSITION = 7
    RELATIVE_TO_NEXT_EXCLUSIVE = 1
    RELATIVE_TO_NEXT_INCLUSIVE = 2
    RELATIVE_TO_NEIGHBORS = 3
    RELATIVE_TO_SIBLINGS = 4
    LONGEST_ORDERED_SUBSEQUENCE = 5
    LONGEST_CONNECTED_SUBSEQUENCE = 6

    @classmethod
    def from_str(cls, value: str) -> "GradingType":
        return cls[value.upper()] if value else cls.ALL_OR_NOTHING

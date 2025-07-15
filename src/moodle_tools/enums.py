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


class ScoreMode(StrEnum):
    SET = "="
    ADD = "+"
    SUBTRACT = "-"

    @classmethod
    def from_str(cls, value: str) -> "ScoreMode":
        return cls[value.upper()] if value else cls.SET


class STACKMatchType(StrEnum):
    ALG_EQUIV = "AlgEquiv"
    ALG_EQUIV_NOUNS = "AlgEquivNouns"
    SUBST_EQUIV = "SubstEquiv"
    CAS_EQUAL = "CasEqual"
    SAME_TYPE = "SameType"
    SYS_EQUIV = "SysEquiv"
    FAC_FORM = "FacForm"
    PART_FRAC = "PartFrac"
    SINGLEF_RAC = "SingleFrac"
    COMP_SQUARE = "CompSquare"
    EXPANDED = "Expanded"
    LOWEST_TERMS = "LowestTerms"
    EQUAL_COMASS = "EqualComAss"
    EQUAL_COMASSRULES = "EqualComAssRules"
    NUM_RELATIVE = "NumRelative"
    NUM_ABSOLUTE = "NumAbsolute"
    NUM_SIG_FIGS = "NumSigFigs"
    NUM_DEC_PLACES = "NumDecPlaces"
    NUM_DEC_PLACES_WRONG = "NumDecPlacesWrong"
    SIG_FIGS_STRICT = "SigFigsStrict"
    GREATER_THAN = "GT"
    GREATER_THAN_EQUALS = "GTE"
    UNITS = "Units"
    UNITS_STRICT = "UnitsStrict"
    UNITS_RELATIVE = "UnitsRelative"
    UNITS_STRICT_RELATIVE = "UnitsStrictRelative"
    UNITS_ABSOLUTE = "UnitsAbsolute"
    UNITS_STRICT_ABSOLUTE = "UnitsStrictAbsolute"
    DIFFERENTIATE = "Diff"
    INTEGRATE = "Int"
    ANTIDIFF = "Antidiff"
    ADD_CONST = "AddConst"
    STRING = "String"
    STRING_SLOPPY = "StringSloppy"
    LEVENSHTEIN = "Levenshtein"
    S_REGEXP = "SRegExp"
    SETS = "Sets"
    EQUIV = "Equiv"
    EQUIV_FIRST = "EquivFirst"
    PROP_LOGIC = "PropLogic"

    @classmethod
    def from_str(cls, value: str) -> "STACKMatchType":
        return cls[value.upper()] if value else cls.ALG_EQUIV


class CRGrader(StrEnum):
    EQUALITY_GRADER = "EqualityGrader"
    NEAR_EQUALITY_GRADER = "NearEqualityGrader"
    REGEX_GRADER = "RegexGrader"
    TEMPLATE_GRADER = "TemplateGrader"

    @classmethod
    def from_str(cls, value: str) -> "CRGrader":
        return cls[value.upper()] if value else cls.EQUALITY_GRADER

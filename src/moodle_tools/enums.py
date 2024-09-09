from enum import StrEnum, auto


class ShuffleAnswersEnum(StrEnum):
    SHUFFLE = auto()
    IN_ORDER = auto()
    LEXICOGRAPHICAL = auto()

    @staticmethod
    def from_str(value: str) -> "ShuffleAnswersEnum":
        return ShuffleAnswersEnum[value.upper()]

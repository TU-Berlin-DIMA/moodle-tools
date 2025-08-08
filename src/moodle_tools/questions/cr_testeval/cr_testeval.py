from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CRDisplayType(StrEnum):
    SHOW = "SHOW"
    HIDE = "HIDE"
    HIDE_IF_SUCCEED = "HIDE_IF_SUCCEED"
    HIDE_IF_FAIL = "HIDE_IF_FAIL"

    @classmethod
    def from_str(cls, value: str) -> "CRDisplayType":
        """Convert a string to a DisplayType enum."""
        return cls(value.upper()) if value else cls.SHOW


@dataclass
class CRTestCase:
    testcode: str
    extra: str
    expected_result: str
    testcase_max: float
    additional_info: dict[str, Any] | None
    hide_rest_if_fail: bool
    display: CRDisplayType


class CRTestEval(ABC):
    @staticmethod
    @abstractmethod
    def evaluate_testcase(
        testcase: CRTestCase,
        student_answer: str,
        hide_rest_if_fail: bool,
        **kwargs: str | int,
    ) -> tuple[str, str, bool, list[str]]:
        """Evaluate a single test case.

        Args:
            testcase: The test case to evaluate.
            student_answer: The student's answer to be evaluated.
            hide_rest_if_fail: Whether to hide the rest of the test cases if this one fails.
            kwargs: Additional keyword arguments for evaluation.

        Returns:
            - A tuple containing:
                - str: The received result.
                - str: The expected result.
                - bool: Whether the test case passed.
                - list[str]: Any errors encountered during evaluation.
        """

from moodle_tools.enums import ScoreMode, STACKMatchType
from moodle_tools.questions.stack_subquestions.dataclasses import (
    PRT,
    Input,
    PRTNode,
    PRTNodeBranch,
)
from moodle_tools.questions.stack_subquestions.stack_subquestion import STACKSubQuestion
from moodle_tools.utils import parse_markdown


class DifferentiatedSetEqualitySubQuestion(STACKSubQuestion):
    """A Differentiated Set Equivalence question type for Moodle based on STACK.

    This question type checks if the expected set matches the received set fully,
    giving partial points if not.
    """

    def __init__(
        self,
        expected_set: list[str],
        additional_sets_until_wrong: int = 0,
        grade: float = 1.0,
        subset_prefix: str = "r",
        expected_answer_var: str = "expected",
        received_answer_var: str = "received",
        prt_name: str = "prt1",
    ) -> None:
        super().__init__(
            grade=grade,
            subset_prefix=subset_prefix,
            expected_answer_var=expected_answer_var,
            received_answer_var=received_answer_var,
            prt_name=prt_name,
        )

        self.subset_prefix = subset_prefix
        self.expected_answer_var = expected_answer_var
        self.received_answer_var = received_answer_var
        self.prt_name = prt_name

        self.question_note = parse_markdown(f"{{@{self.expected_answer_var}@}}")
        self.specific_feedback = parse_markdown(f"[[feedback:{self.prt_name}]]")

        self.inputs = {
            self.received_answer_var: Input(
                type="algebraic",
                matching_answer_variable=self.expected_answer_var,
                width=len(", ".join(expected_set)) + 30,
            ),
        }

        variables_terms_set = self.build_input_variables(expected_set)

        self.build_prt(additional_sets_until_wrong, variables_terms_set)

    def build_input_variables(self, expected_set: list[str]) -> list[tuple[str, str]]:
        variables_terms_set = list(
            zip(
                [f"{self.subset_prefix}{i}" for i in range(1, len(expected_set) + 1)],
                expected_set,
                strict=False,
            )
        )
        self.input_variables = [f"{var}: {set_part}" for var, set_part in variables_terms_set]
        self.input_variables.append(
            f"{self.expected_answer_var}: {{ {','.join([v[0] for v in variables_terms_set])} }}"
        )
        return variables_terms_set

    def build_prt(
        self, additional_sets_until_wrong: int, numbered_set: list[tuple[str, str]]
    ) -> None:
        response_nodes = {
            num: PRTNode(
                test_type=STACKMatchType.SETS,
                received_answer=f"intersection(set({current_subset}), {self.received_answer_var})",
                expected_answer=f"set({current_subset})",
                true_branch=PRTNodeBranch(
                    score_mode=ScoreMode.ADD,
                    score=1 / len(numbered_set) * self.grade,
                    next_node=num + 1,
                    answer_note=f"{self.prt_name}-{current_subset}-correct",
                ),
                false_branch=PRTNodeBranch(
                    score_mode=ScoreMode.ADD,
                    score=0,
                    next_node=num + 1,
                    answer_note=f"{self.prt_name}-{current_subset}-wrong",
                ),
            )
            for (current_subset, _), num in zip(
                numbered_set, range(len(numbered_set)), strict=False
            )
        }
        too_many_sets_nodes = {
            num + len(response_nodes): PRTNode(
                test_type=STACKMatchType.GREATER_THAN,
                received_answer=f"cardinality({self.received_answer_var})",
                expected_answer=f"cardinality({self.expected_answer_var}) + {num}",
                true_branch=PRTNodeBranch(
                    score_mode=ScoreMode.SUBTRACT,
                    score=1 / (additional_sets_until_wrong + 1) * self.grade,
                    next_node=num + len(response_nodes) + 1
                    if num < additional_sets_until_wrong
                    else -1,
                    answer_note=f"{self.prt_name}-{num + 1}-GT-toomany",
                ),
                false_branch=PRTNodeBranch(
                    score_mode=ScoreMode.ADD,
                    score=0,
                    next_node=-1,
                    answer_note=f"{self.prt_name}-{num}-LEQ-toomany",
                ),
            )
            for num in range(additional_sets_until_wrong + 1)
        }
        response_nodes.update(too_many_sets_nodes)
        self.response_trees = {
            self.prt_name: PRT(
                max_points=self.grade,
                nodes=response_nodes,
            )
        }

from moodle_tools.enums import ScoreMode, STACKMatchType
from moodle_tools.questions.diff_set_equality import DifferentiatedSetEquality
from moodle_tools.questions.stack import PRT, PRTNode, PRTNodeBranch


class ExactSetEquality(DifferentiatedSetEquality):
    """An Exact Set Equality question type for Moodle based on STACK.

    This question type checks if the expected set matches the received fully,
    giving no partial points.
    """

    def build_input_variables(self, expected_set: list[str]) -> list[tuple[str, str]]:
        self.input_variables.append(
            f"{self.expected_answer_var}: {{ {','.join([v[0] for v in expected_set])} }}"
        )

        return []

    def build_prt(
        self, additional_sets_until_wrong: int, numbered_set: list[tuple[str, str]]
    ) -> None:
        self.response_trees = {
            self.prt_name: PRT(
                max_points=1.0,
                nodes={
                    0: PRTNode(
                        test_type=STACKMatchType.SETS,
                        received_answer=self.received_answer_var,
                        expected_answer=self.expected_answer_var,
                        true_branch=PRTNodeBranch(
                            score_mode=ScoreMode.SET,
                            score=1.0,
                            answer_note=f"{self.prt_name}-{self.expected_answer_var}-correct",
                        ),
                        false_branch=PRTNodeBranch(
                            score_mode=ScoreMode.SET,
                            score=0.0,
                            answer_note=f"{self.prt_name}-{self.expected_answer_var}-wrong",
                        ),
                    )
                },
            )
        }

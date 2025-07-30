from dataclasses import dataclass, field

from moodle_tools.questions.stack_subquestions.dataclasses import PRT, Input


@dataclass
class STACKSubQuestion:
    grade: float
    subset_prefix: str
    expected_answer_var: str
    received_answer_var: str
    prt_name: str
    input_variables: list[str] = field(default_factory=list)
    inputs: dict[str, Input] = field(default_factory=dict)
    response_trees: dict[str, PRT] = field(default_factory=dict)

from dataclasses import dataclass, field

from moodle_tools.enums import ScoreMode, STACKMatchType


@dataclass
class PRTNodeBranch:
    score_mode: ScoreMode
    score: float
    penalty: str = ""
    answer_note: str = ""
    feedback: str = ""
    next_node: int = -1


@dataclass
class PRTNode:
    test_type: STACKMatchType
    received_answer: str
    expected_answer: str
    true_branch: PRTNodeBranch
    false_branch: PRTNodeBranch
    description: str = ""
    test_options: str = ""
    quiet: bool = True


@dataclass
class PRT:
    max_points: float
    nodes: dict[int, PRTNode]
    auto_simplify: bool = True
    feedback_style: int = 1
    feedback_variables: list[str] = field(default_factory=list)


@dataclass
class Input:
    type: str
    matching_answer_variable: str
    width: int
    strict_syntax: bool = True
    insert_stars: bool = False
    syntax_hint: str = ""
    syntax_attribute: bool = False
    forbidden_words: list[str] = field(default_factory=list)
    allowed_words: list[str] = field(default_factory=list)
    forbid_floats: bool = True
    require_lowest_terms: bool = False
    check_answer_type: bool = False
    must_verify: bool = True
    show_validation: int = 2
    options: list[str] = field(default_factory=list)

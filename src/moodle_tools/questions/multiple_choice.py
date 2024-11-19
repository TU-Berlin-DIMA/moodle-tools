from moodle_tools.questions.numerical import NumericalQuestion
from moodle_tools.questions.question import QuestionAnalysis
from moodle_tools.utils import preprocess_text


class MultipleChoiceQuestion(NumericalQuestion):
    """General template for a multiple choice question with a single selection."""

    QUESTION_TYPE = "multichoice"
    XML_TEMPLATE = "multiple_choice.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answers: list[str],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "Your answer is correct.",
        partially_correct_feedback: str = "Your answer is partially correct.",
        incorrect_feedback: str = "Your answer is incorrect.",
        shuffle_answers: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(
            question=question,
            title=title,
            answers=answers,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            **flags,
        )
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partially_correct_feedback = preprocess_text(partially_correct_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)
        self.shuffle_answers = shuffle_answers

        # Inline images
        for answer in self.answers:
            answer["answer"] = preprocess_text(answer["answer"], **flags)


class MultipleChoiceQuestionAnalysis(QuestionAnalysis):
    def normalize_question(self, question_text: str) -> str:
        return question_text[: question_text.rindex(":")]

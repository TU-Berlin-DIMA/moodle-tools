import argparse
import csv
import re
import sys
from collections import Counter, namedtuple
from statistics import median


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input file (default: %(default)s)",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: %(default)s)",
        type=argparse.FileType("w"),
        default=sys.stdout,
    )
    parser.add_argument(
        "--n",
        "--numeric",
        help="List of numeric questions",
        action="extend",
        nargs="*",
        type=NumericQuestion,
        default=[],
    )
    parser.add_argument(
        "--tf",
        "--true-false",
        help="List of True/False questions",
        action="extend",
        nargs="*",
        type=TrueFalseQuestion,
        default=[],
    )
    parser.add_argument(
        "--mc",
        "--multiple-choice",
        help="List of multiple choice questions",
        action="extend",
        nargs="*",
        type=MultipleChoiceQuestion,
        default=[],
    )
    parser.add_argument(
        "--mtf",
        "--multiple-true-false",
        help="List of multiple choice questions",
        action="extend",
        nargs="*",
        type=MultipleTrueFalseQuestion,
        default=[],
    )
    parser.add_argument(
        "--dd",
        "--drop-down",
        help="List of drop-down questions",
        action="extend",
        nargs="*",
        type=DropDownQuestion,
        default=[],
    )
    parser.add_argument(
        "--mw",
        "--missing-words",
        help="List of missing words questions",
        action="extend",
        nargs="*",
        type=MissingWordsQuestion,
        default=[],
    )
    parser.add_argument(
        "--cloze",
        help="List of cloze questions",
        action="extend",
        nargs="*",
        type=ClozeQuestion,
        default=[],
    )
    parser.add_argument(
        "--cr",
        "--coderunner",
        help="List of coderunner questions",
        action="extend",
        nargs="*",
        type=CoderunnerQuestionSQL,
        default=[],
    )
    args = parser.parse_args()
    args.handlers = (
        args.n + args.tf + args.mc + args.mtf + args.dd + args.cloze + args.mw
    )
    return args


class Question(
    namedtuple(
        "Question",
        [
            "question_number",
            "variant_number",
            "question",
            "subquestion",
            "correct_response",
        ],
    )
):
    def __eq__(self, other):
        return self.question == other.question and self.subquestion == other.subquestion

    def __hash__(self):
        return hash((self.question, self.subquestion))


class BaseQuestion:
    def __init__(self, question_number):
        self.question_number = question_number
        self.questions = {}
        self.question_texts = []

    def process_response(self, question_text, response, right_answer):
        response = self.normalize_response(response)
        question_text = self.normalize_question_text(question_text)
        right_answer = self.normalize_response(right_answer)
        question = self.add_question(question_text, "", right_answer)
        if question:
            self.add_response(question, response)

    def add_question(self, question_text, sub_question_text, right_answer):
        if question_text not in self.question_texts:
            self.question_texts.append(question_text)
        question = Question(
            self.question_number,
            len(self.question_texts),
            question_text,
            sub_question_text,
            right_answer,
        )
        if question not in self.questions:
            self.questions[question] = Counter()
        return question

    def add_response(self, question, response):
        self.questions[question][response] += 1

    def normalize_response(self, response):
        return response

    def normalize_question_text(self, question_text):
        return question_text

    def grade(self, responses, correct_answer):
        total = sum(responses.values())

        def correct_responses(responses, correct_answer):
            grade = responses[correct_answer]
            if re.match(r"^([0-9]*)?\.[0-9]+$", correct_answer):
                grade += responses[correct_answer.replace(".", ",")]
            elif re.match(r"^([0-9]*)?,[0-9]+$", correct_answer):
                grade += responses[correct_answer.replace(",", ".")]
            return grade

        return {
            "grade": correct_responses(responses, correct_answer) / total * 100,
            "occurrence": total,
            "responses": dict(responses),
        }


class NumericQuestion(BaseQuestion):
    pass


class TrueFalseQuestion(BaseQuestion):
    pass


class CoderunnerQuestionSQL(BaseQuestion):
    pass


class MultipleChoiceQuestion(BaseQuestion):
    def normalize_question_text(self, question_text):
        return question_text[: question_text.rindex(":")]


class MultipleResponseQuestion(BaseQuestion):
    def __init__(self, question_number, answer_re, separator):
        super().__init__(question_number)
        self.answer_re = answer_re + separator
        self.separator = separator

    def process_response(self, question_text, response, right_answer):
        question_text = self.normalize_question_text(question_text)
        responses = self.normalize_answers(response)
        right_answers = self.normalize_answers(right_answer)
        for subquestion_text, subquestion_right_answer in right_answers.items():
            subquestion = self.add_question(
                question_text, subquestion_text, subquestion_right_answer
            )
            if subquestion:
                self.add_response(subquestion, responses.get(subquestion_text, "-"))

    def normalize_answers(self, response):
        answers = {}
        if not response:
            return answers
        response += self.separator
        for match in re.finditer(self.answer_re, response, re.MULTILINE + re.DOTALL):
            subquestion_text, subquestion_answer = match.group(1), match.group(2)
            subquestion_text = self.normalize_subquestion_text(subquestion_text.strip())
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers

    def normalize_question_text(self, question_text):
        return question_text

    def normalize_subquestion_text(self, subquestion_text):
        return subquestion_text


class MultipleTrueFalseQuestion(MultipleResponseQuestion):
    def __init__(self, question_number):
        super().__init__(question_number, r"(.*?)\n?: (False|Falsch|True|Wahr)", "; ")


class DropDownQuestion(MultipleResponseQuestion):
    def __init__(self, question_number):
        super().__init__(question_number, r"(.*?)\n -> (.*?)", ";")

    def normalize_question_text(self, question_text):
        question_text = question_text.replace("\n", " ")
        question_text = re.sub("{.*} -> {.*}", "", question_text, re.DOTALL)
        return question_text


class ClozeQuestion(MultipleResponseQuestion):
    def __init__(self, question_number):
        super().__init__(question_number, r"(.*?): (.*?)", "; ")


class MissingWordsQuestion(MultipleResponseQuestion):
    def __init__(self, question_number):
        super().__init__(question_number, r"{(.*?)}", " ")

    def normalize_answers(self, response):
        answers = {}
        if not response:
            return answers
        response += self.separator
        for i, match in enumerate(re.finditer(self.answer_re, response, re.MULTILINE)):
            subquestion_answer = match.group(1)
            subquestion_text = str(i)
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers


def normalize_questions(infile, outfile, handlers):
    # Process responses from input CSV file
    for row in csv.DictReader(infile, delimiter=",", quotechar='"'):
        for handler in handlers:
            q_num = handler.question_number
            handler.process_response(
                row[f"Question {q_num}"],
                row[f"Response {q_num}"],
                row[f"Right answer {q_num}"],
            )
    # Sort and flatten normalized questions and determine grades
    questions = [
        (question, handler.grade(responses, question.correct_response))
        for handler in sorted(handlers, key=lambda x: int(x.question_number))
        for question, responses in handler.questions.items()
    ]
    # Determine median grade and MAD
    grades = [grade["grade"] for _, grade in questions]
    median_grade = median(grades)
    mad = median([abs(grade - median_grade) for grade in grades])
    print(f"Median grade: {median_grade:1.1f}, MAD: {mad:1.1f}", file=sys.stderr)
    # Write normalized results as CSV file
    fieldnames = [
        "question_number",
        "variant_number",
        "question",
        "subquestion",
        "correct_response",
        "grade",
        "outlier",
        "occurrence",
        "responses",
    ]
    writer = csv.DictWriter(outfile, fieldnames, dialect=csv.excel_tab)
    writer.writeheader()
    for question, grade in questions:
        row = question._asdict()
        grade["outlier"] = not (
            median_grade - 2 * mad <= grade["grade"] <= median_grade + 2 * mad
        )
        row.update(grade)
        writer.writerow(row)


def main() -> None:
    args = parse_args()
    custom_handlers: list[BaseQuestion] = []
    normalize_questions(args.input, args.output, args.handlers + custom_handlers)


if __name__ == "__main__":
    main()

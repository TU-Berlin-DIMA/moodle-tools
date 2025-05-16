from typing import TypedDict

from moodle_tools.enums import EditorType, PredefinedFileTypes
from moodle_tools.questions.question import Question
from moodle_tools.utils import ParsingError, parse_filesize, preprocess_text


class TextResponse(TypedDict, total=False):
    """TypedDict for text response."""

    required: bool
    template: str
    min_words: int | str
    max_words: int | str
    allow_media_in_text: bool


class FileResponse(TypedDict, total=False):
    """TypedDict for file response."""

    number_allowed: int
    number_required: int
    max_size: int | str
    max_size_bytes: int
    accepted_types: list[str]
    required: bool


class EssayQuestion(Question):
    """General template for an Essay question."""

    QUESTION_TYPE = "essay"
    XML_TEMPLATE = "essay.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        response_format: EditorType,
        text_response: TextResponse | None = None,
        file_response: FileResponse | None = None,
        grader_info: str = "",
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)

        self.response_format = EditorType.from_str(response_format)
        self.text_response = text_response
        self.file_response = file_response
        self.grader_info = preprocess_text(grader_info, **flags)

        self.handle_text_response()
        self.handle_file_response()

    def handle_text_response(self) -> None:
        resp = self.text_response

        if resp and self.response_format == EditorType.NOINLINE:
            raise ParsingError("Response format NOINLINE does not support text response.")

        if not resp:
            self.text_response = {
                "required": False,
                "template": "",
                "min_words": "",
                "max_words": "",
                "allow_media_in_text": False,
            }
            return

        resp["template"] = preprocess_text(str(resp.get("template", "")), **self.flags)

        allow_media_in_text = resp.get("allow_media_in_text", False)

        if (
            self.response_format not in [EditorType.EDITOR, EditorType.EDITORFILEPICKER]
            and allow_media_in_text
        ):
            raise ParsingError(
                "Response format {} does not support media in text response.", self.response_format
            )
        if not allow_media_in_text and self.response_format == EditorType.EDITORFILEPICKER:
            raise ParsingError(
                "You chose the response format EDITORFILEPICKER and do not want to "
                "allow media in text. This is not allowed."
            )
        if self.response_format == EditorType.EDITOR and allow_media_in_text:
            self.response_format = EditorType.EDITORFILEPICKER

        if (
            resp.get("min_words")
            and resp.get("max_words")
            and int(resp.get("min_words", 0)) > int(resp.get("max_words", 1))
        ):
            raise ParsingError("Minimum words cannot be greater than maximum words.")

    def handle_file_response(self) -> None:
        resp = self.file_response

        if not resp:
            return

        number_allowed = resp.get("number_allowed", -1)
        number_required = resp.get("number_required", 0)

        resp["number_allowed"] = number_allowed
        resp["max_size_bytes"] = parse_filesize(resp.get("max_size", 0))

        accepted_types = resp.get("accepted_types", [])

        predefined_types = [
            PredefinedFileTypes.from_str(f) for f in accepted_types if not f.startswith(".")
        ]

        if any(pt == PredefinedFileTypes.NONE for pt in predefined_types):
            raise ParsingError("Predefined file types cannot be NONE.")

        file_endings = [f for f in accepted_types if f.startswith(".")]
        resp["accepted_types"] = predefined_types + file_endings

        if number_allowed > number_required and number_allowed != -1:
            raise ParsingError(
                "Number of files required cannot be greater than number of files allowed."
            )

    def validate(self) -> list[str]:
        error_list = super().validate()

        if not self.grader_info:
            error_list.append("No grader info provided.")

        if self.response_format == EditorType.NOINLINE and not self.file_response:
            error_list.append("Response format NOINLINE should have a file response.")

        return error_list

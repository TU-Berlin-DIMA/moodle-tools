import moodle_tools.questions as Questions


class QuestionFactory:
    @staticmethod
    def create_question(question_type, **properties):
        match question_type:
            case "true_false":
                return Questions.TrueFalseQuestion(**properties)
            case "multiple_true_false":
                return Questions.MultipleTrueFalseQuestion(**properties)
            case "multiple_choice":
                return Questions.SingleSelectionMultipleChoiceQuestion(**properties)
            case "cloze":
                return Questions.ClozeQuestion(**properties)
            case "numerical":
                return Questions.NumericalQuestion(**properties)
            case "missing_words":
                return Questions.MissingWordsQuestion(**properties)
            case "coderunner":
                return Questions.CoderunnerQuestionSQL(**properties)
            case _:
                return "Something's wrong with the internet"

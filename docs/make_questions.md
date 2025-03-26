# Generate Moodle Quiz Questions

This tool allows the generation of (multiple) Moodle quiz questions from one or multiple YAML documents.
The questions can be imported into a YAML-defined or individually selected question category in Moodle.
We can then create a quiz entry which randomly selects a question from the question category.

- [Workflow](#workflow)
- [Question types](#question-types)
- [Command line usage](#command-line-usage)

## Workflow

### Step 0 (optional): Create a question category

The variants of a single question should all go into a dedicated question category.

Best practice is to create a top-level category for each examination element (e.g., `2022-T1-1` in the screenshot), then a subcategory which groups similar questions (e.g., `Normalisierung`), and then the question categories as the third level (e.g., `Hülle und Basis`.)

**Note:** Creating question categories via the Moodle UI is optional. You can also define question
categories via the YAML keyword `category`. Category hierachies can be specified by separating
categories with a `/`. Note that if you specify a `category` for one question, all following questions
will be added to the same category unless you specify another `category` for them.

![Question categories](assets/question-categories.png)

### Step 1: Create a YAML document with questions

Moodle quiz questions are generated from YAML files.
In a later step, these are converted to Moodle XML and then imported into the Moodle course.

The format of these YAML file depends on the question type and is described below.

The variants for a single question can be collected into a single YAML file.
(It is also to possible to use multiple YAML files.)

In the example below, there are two question variants for a multiple true/false question, and each variant is separated by three dashes `---`.

Store the following YAML contents in a file `example.yml`:

```yaml
---
type: multiple_true_false
question: |
  <p>
  Welche der folgenden Operationen gehören zu den Basisoperatoren der Relationalen Algebra?
  </p>
title: Relationale Algebra 1
answers:
  - answer: Projektion
    choice: True
  - answer: Division
    choice: False
  - answer: Natürlicher Join
    choice: False
---
question: |
  <p>
  Welche der folgenden Operationen gehören zu den Basisoperatoren der Relationalen Algebra?
  </p>
title: Relationale Algebra 2
answers:
  - answer: Differenz
    choice: True
  - answer: Vereinigung
    choice: True
  - answer: Schnitt
    choice: False
```

### Step 2: Convert the YAML files to Moodle XML

Since the question variants in the example above are multiple true/false questions, we use the
`multiple_true_false` question type:

```bash
make-questions -i example.yml -o example.xml -s
```

### Step 3: Import the questions into Moodle

Import the generated Moodle XML into a Moodle course.
The questions that are already in the question category of your choice remain unchanged.
This means that if you want to update your questions, you should first delete the old questions in the category.

![Import questions into Moodle](assets/import-questions.png)

### Step 4: Add the questions to a Moodle quiz

To use your question (variants) in a quiz, add a random question from the question category.
It is possible to use more than one question variant.

![Add random question](assets/add-random-question-1.png)

![Add random question](assets/add-random-question-2.png)

## Question Types

At the moment, the following question types are supported.

- Description
- Simple true/false questions
- Multiple choice questions with a single selection
- Multiple true/false questions
- Numerical questions
- Short Answer questions
- Missing words questions
- Cloze questions

The following question types are supported if you install the `isda` extra dependencies:

- CodeRunner SQL-DQL
- CodeRunner SQL-DDL/DML
- CodeRunner ISDA Streaming

Multiple question variants can be collected in a single YAML document.
In this case, each question variant is separated by three dashes `---`.

### Description

This question type just provides a text field to write some information. It does not have any answer options or similar.

The full YAML format for such a question is as follows:

```yaml
type: description   # Mandatory
category: category/subcategory/description    # Optional
title: Description title    # Mandatory
question: Complete description    # Mandatory
```

### Simple true/false questions

This question type specifies a simple true/false question.

The full YAML format for such a question is as follows:

```yaml
type: true_false   # Mandatory
category: category/subcategory/true_false    # Optional
title: Question title    # Mandatory
question: Complete question    # Mandatory
correct_answer: false    # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
correct_feedback: Correct feedback  # Mandatory in strict mode
incorrect_feedback: Wrong feedback  # Mandatory in strict mode
```

This YAML content is rendered as follows in Moodle:

![Simple true/false question](assets/simple-true-false.png)

It is possible to shorten the specification to only include the question type, the question text, and the correct answer.
This requires the skip-strict-mode to be true, either by using the `-s` argument in the CLI or by declaring it in the YAML document:

```yaml
type: true_false
question: "Minimal false question"
correct_answer: false
skip_validation: true   # Optional
```

Furthermore, if the correct answer is true, it is possible to shorten the specification even more:

```yaml
type: true_false
question: "Minimal true question"
```

### Multiple choice questions

This question type specifies a multiple choice question in which the student can only select one answer.
Moodle renders a radio button next to each answer.

Note that the `points` attribute for each answer is optional.
However, it is only valid to specify points for all OR none of the answers within a question.
If you do not specify `points`, the first answer is assumed the correct one and the others are assumed incorrect.

The full YAML format for such a question is as follows:

```yaml
type: multiple_choice  # Mandatory
category: category/subcategory/multiple_choice  # Optional
title: Question title  # Mandatory
question: Extended format  # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
shuffle_answers: True  # Optional
answers:  # Mandatory
  - answer: Correct answer  # Mandatory
    points: 100  # Optional
    feedback: Feedback for option 1  # Mandatory in strict mode
  - answer: Partial answer  # Mandatory
    points: 50  # Optional
    feedback: Feedback for option 2  # Mandatory in strict mode
  - answer: Wrong answer  # Mandatory
    points: 0  # Optional
    feedback: Feedback for option 3  # Mandatory in strict mode
```

This YAML content is rendered as follows in Moodle:

![Multiple choice question with a single selection](assets/multiple-choice.png)

As the example shows, it is possible to assign a number of points for each answer.
100 points indicate a correct answer and 0 points a wrong answer; anything in between is partial credit.

It is possible to shorten the specification to only include the question type, the question text, and the answer text.
The first answer is assumed to be correct (100 points), the remaining answers are assumed to be false (0 points).

For all the simple formats it is mandatory to raise the skip-strict-mode flag.

```yaml
type: multiple_choice
question: Simple format
answers:
  - Correct answer 1
  - Wrong answer 1
  - Wrong answer 2
```

### Multiple true/false questions

This question types specifies a question which contains multiple answers.
For each answer, the student has to indicate whether it is true of false.

This question should be used instead of specifying a multiple choice question with multiple correct answers (sinceMoodle would render those using checkboxes, allowing the student to select multiple answers).
The reason is that the examination guidelines do not allow us to subtract points for false answers.
Therefore, students could simply select all possible answers and get full credit.
This strategy is not possible with this question type.

The full YAML format for such a question is as follows:

```yaml
type: multiple_true_false  # Mandatory
category: category/subcategory/true_false  # Optional
title: Title  # Mandatory
question: Simple format  # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
answers:  # Mandatory
  - answer: Answer 1  # Mandatory
    choice: True  # Mandatory
    feedback: None  # Mandatory in strict mode
  - answer: Answer 2  # Mandatory
    choice: False  # Mandatory
    feedback: None  # Mandatory in strict mode
```

It is possible to shorten the specification to only include the question type, the question text, and the answers.

```yaml
type: multiple_true_false
question: Simple format
answers:
  - answer: Answer 1
    choice: True
  - answer: Answer 2
    choice: False
```

It is also possible to rename the choices.
The default choices are `True` and `False`.
The example below uses `Ascending` and `Descending` instead.

```yaml
type: multiple_true_false  # Mandatory
category: category/subcategory/true_false  # Optional
title: Memory hierarchy  # Mandatory
question: For each category, say descending or ascending  # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
shuffle_answers: True  # Optional
choices: [Ascending, Descending]   # Optional
answers:  # Mandatory
  - answer: Cost  # Mandatory
    choice: Ascending  # Mandatory
    feedback: Feedback  # Mandatory in strict mode
  - answer: Latency  # Mandatory
    choice: Descending  # Mandatory
    feedback: Feedback  # Mandatory in strict mode
```

It is also possible to specify more than two choices.
The example below uses three choices.
Note that `Yes` and `No` are escaped with `!!str`.
Without the escape, the YAML parser would treat them as `True` and `False`.

```yaml
type: multiple_true_false  # Mandatory
category: category/subcategory/true_false  # Optional
title: Title  # Mandatory
question: Extended format  # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
shuffle_answers: False  # Optional
choices: [!!str Yes, !!str No, Maybe]  # Optional
answers:  # Mandatory
  - answer: Answer 1  # Mandatory
    choice: !!str Yes  # Mandatory
    feedback: Feedback 1  # Mandatory in strict mode
  - answer: Answer 2  # Mandatory
    choice: !!str No  # Mandatory
    feedback: Feedback 2  # Mandatory in strict mode
  - answer: Answer 3  # Mandatory
    choice: Maybe  # Mandatory
    feedback: Feedback 3  # Mandatory in strict mode
```

This YAML content is rendered as follows in Moodle:

![Multiple true/false question](assets/multiple-true-false.png)

### Numerical questions

This question type expects a numerical value as the answer.
It is possible to add tolerances to each answer.
Moodle will then evaluate the answer as correct if it is +/- the tolerance value.

The full YAML format for such a question is as follows:

```yaml
type: numerical  # Mandatory
category: category/subcategory/numerical  # Optional
title: Numerical question  # Mandatory
question: What is 2 + 2?  # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
answers:  # Mandatory
  - answer: 4  # Mandatory
    tolerance: 0   # Optional
    points: 100  # Optional
    feedback: Feedback for first answer  # Mandatory in strict mode
  - answer: 5  # Mandatory
    tolerance: 0.1  # Optional
    points: 50  # Optional
    feedback: 2 + 2 = 5 for some values of 2  # Mandatory in strict mode
```

This YAML content is rendered as follows in Moodle:

![Numerical question](assets/numerical.png)

As the example shows, it is possible to assign a number of points for each answer.
100 points indicate a correct answer and 0 points a wrong answer; anything in between is partial credit.

It is possible to shorten the specification to only include the question type, the question text, and the answers.
The first answer is assumed to be correct (100 points), the remaining answers are assumed to be false (0 points).
The tolerance for every answer is 0.

```yaml
type: numerical
question: What is 2 + 2?
answers:
  - 4
  - 22
```

Further, it is possible to inline the answer field by specifying `[[ANSWERBOX]]` in the question text.
Moodletools will automatically replace this placeholder with an answer box of width 10 by inserting 10 underscores at this location.
If you specify a number after the placeholder (e.g. `[[ANSWERBOX=6]]` for an answerbox of width 6), the width of the answer box will be set to this number.
The answerbox will always have a width of at least 5.
For furter information on the answerbox, see the [Moodle documentation](https://docs.moodle.org/404/en/Short-Answer_question_type).
Using underscores in the answer to specify the length of the answer box is not recommended, as non-escaped underscores will be interpreted by the markdown parser as italics or bold text.

### Short answer questions

This question type expects a short text as the answer.
By default, Moodle will render a text box below the question, where students will put their answer.

The full YAML format for such a question is as follows:

```yaml
type: shortanswer  # Mandatory
title: Short Answer question  # Mandatory
question: How does an SQL query start?  # Mandatory
general_feedback: General feedback  # Mandatory in strict mode
answer_case_sensitive: false  # Optional
answers:  # Mandatory
  - answer: SELECT  # Mandatory
    points: 100  # Optional
    feedback: Correct  # Mandatory in strict mode
  - answer: WITH  # Mandatory
    points: 50  # Optional
    feedback: Only if you have a CTE  # Mandatory in strict mode
```

This YAML content is rendered as follows in Moodle:

![Short answer question](assets/shortanswer.png)

As the example shows, it is possible to assign a number of points for each answer.
100 points indicate a correct answer and 0 points a wrong answer; anything in between is partial credit.
It is also possible to specify whether the answer is case sensitive or not.

Further, it is possible to inline the answer field by specifying `[[ANSWERBOX]]` in the question text.
Moodletools will automatically replace this placeholder with an answer box of width 10 by inserting 10 underscores at this location.
If you specify a number after the placeholder (e.g. `[[ANSWERBOX=6]]` for an answerbox of width 6), the width of the answer box will be set to this number.
The answerbox will always have a width of at least 5.
For furter information on the answerbox, see the [Moodle documentation](https://docs.moodle.org/404/en/Short-Answer_question_type).
Using underscores in the answer to specify the length of the answer box is not recommended, as non-escaped underscores will be interpreted by the markdown parser as italics or bold text.

It is possible to shorten the specification to only include the question type, the question text, and the answers.
The first answer is assumed to be correct (100 points), the remaining answers are assumed to be false (0 points).
Note how we are using the `[[ANSWERBOX]]` placeholder in the question text.

```yaml
type: shortanswer
title: Simple Short Answer
question: An SQL query starts with the keyword [[ANSWERBOX=6]].
answers:
  - SELECT
  - FROM
```

### Missing words questions

Missing words questions contain multiple blank places in the question text.
For each blank space, the student has to choose from multiple predefined phrases.

The full YAML format for a missing words question is as follows:

```yaml
type: missing_words  # Mandatory
category: category/subcategory/missing_words  # Optional
title: Missing words question  # Mandatory
shuffle_answers: SHUFFLE # Optional, Alternatives: IN_ORDER, LEXICOGRAPHICAL
question: |-  # Mandatory
  The main clauses of a SQL query are: [[1]] [[2]] [[3]]
general_feedback: General feedback  # Mandatory in strict mode
correct_feedback: Correct feedback  # Mandatory in strict mode
partial_feedback: Partial feedback  # Mandatory in strict mode
incorrect_feedback: Incorrect feedback  # Mandatory in strict mode
options:  # Mandatory
  - answer: SELECT  # Mandatory
    group: 1  # Mandatory
    ordinal: 1  # Optional
  - answer: FROM  # Mandatory
    group: 1  # Mandatory
    ordinal: 2  # Optional
  - answer: WHERE  # Mandatory
    group: 2  # Mandatory
    ordinal: 3  # Optional
  - answer: PROJECT  # Mandatory
    group: 1  # Mandatory
    ordinal: 4  # Optional
  - answer: SIGMA  # Mandatory
    group: 2  # Mandatory
    ordinal: 5  # Optional
```

This YAML content is rendered as follows in Moodle.

![Missing words question](assets/missing-words.png)

The contents of the drop down boxes are defined in the list of `choices`.
The `group` attribute of each choice determines which choices are contained as alternative in a drop-down box.
The references `[[1]]`, `[[2]]`, and `[[3]]` in the question text refer to the indexes of the correct choices for each placeholder.
The result of this definition is that the correct answers for the placeholders are `SELECT`, `FROM`, and `WHERE`.
Furthermore, the choices `SELECT`, `FROM`, and `PROJECT` all belong to group 1 and therefore appear together in the first and second drop-down box.
The third drop-down box consists of the choices `WHERE` and `SIGMA` which belong to group 2.

Shuffle can be one of three values: `SHUFFLE`, `IN_ORDER`, or `LEXICOGRAPHICAL`.

- `SHUFFLE` tasks moodle to shuffle the options in each group.
- `IN_ORDER` leaves the order of the options as they are defined in the YAML file.
- `LEXICOGRAPHICAL` sorts the options in each group lexicographically.

It is possible to omit the feedback attributes.

It is possible to not use solution reference numbers and instead define the answer directly as a string.
In this case, moodletools will automatically resolve the IDs and insert the correct solution reference numbers.

```yaml
type: missing_words
title: Simple missing words question with correct solution in question text and lexicographical ordering
question: |-
  The main clauses of a SQL query are: [["SELECT"]] [["FROM"]] [["WHERE"]]
shuffle_answers: LEXICOGRAPHICAL
options:
  - answer: SELECT
    group: A
  - answer: FROM
    group: A
  - answer: WHERE
    group: A
```

If ordinals are defined with gaps, moodletools will automatically fill the gaps with an unused group and a placeholder value, as seen here:

```yaml
type: missing_words
title: Simple missing words question with gaps in options and in-order ordering
question: |-
  The main clauses of a SQL query are: [[1]] [[2]] [[5]]
shuffle_answers: IN_ORDER
options:
  - answer: SELECT
    group: A
    ordinal: 1
  - answer: FROM
    group: A
    ordinal: 2
  - answer: WHERE
    group: C
    ordinal: 5
```

The options in this yaml file will generate the following xml output:

```xml
<selectoption>
    <text>SELECT</text>
    <group>1</group>
    <!-- ordinal: 1, group: A -->
</selectoption>
<selectoption>
    <text>FROM</text>
    <group>1</group>
    <!-- ordinal: 2, group: A -->
</selectoption>
<selectoption>
    <text>.</text>
    <group>20</group>
    <!-- ordinal: 3, group: T -->
</selectoption>
<selectoption>
    <text>.</text>
    <group>20</group>
    <!-- ordinal: 4, group: T -->
</selectoption>
<selectoption>
    <text>WHERE</text>
    <group>3</group>
    <!-- ordinal: 5, group: C -->
</selectoption>
```

You can observe that the ordinals 3 and 4, which are missing in the yaml file, are automatically added by moodletools.

Similarly, if all references are defined as IDs, moodletools will automatically add gaps of three with an unused group between each group:

```yaml
type: missing_words
title: Simple missing words question with gaps in options and in-order ordering
question: |-
  The main clauses of a SQL query are: [["SELECT"]] [["FROM"]] [["WHERE"]]
shuffle_answers: IN_ORDER
options:
  - answer: SELECT
    group: A
  - answer: FROM
    group: A
  - answer: WHERE
    group: C
```

The options in this yaml file will generate the following xml output:

```xml
<selectoption>
    <text>SELECT</text>
    <group>1</group>
    <!-- ordinal: 1, group: A -->
</selectoption>
<selectoption>
    <text>FROM</text>
    <group>1</group>
    <!-- ordinal: 2, group: A -->
</selectoption>
<selectoption>
    <text>.</text>
    <group>20</group>
    <!-- ordinal: 3, group: T -->
</selectoption>
<selectoption>
    <text>.</text>
    <group>20</group>
    <!-- ordinal: 4, group: T -->
</selectoption>
<selectoption>
    <text>.</text>
    <group>20</group>
    <!-- ordinal: 5, group: T -->
</selectoption>

<selectoption>
    <text>WHERE</text>
    <group>3</group>
    <!-- ordinal: 6, group: C -->
</selectoption>
```

**Note**: This only works properly, if the groups are not scrambled in the yaml file.

### Matching questions

In the [matching questiontype](https://docs.moodle.org/en/Matching_question_type), the student has to match one or multiple given strings to a set of predefined strings.

The full YAML format for a matching question is as follows:

```yaml
type: matching  # Mandatory
category: category/subcategory/matching  # Optional
title: Simple matching question # Mandatory
question: |- # Mandatory
  To which part of a SQL query do these keywords belong to?
shuffle_answers: SHUFFLE # Optional, Alternatives: IN_ORDER, LEXICOGRAPHICAL
general_feedback: General feedback  # Mandatory in strict mode
options: # Mandatory
  - question: SELECT # Mandatory at least 2 times
    answer: DQL # Mandatory at least 3 times
  - question: ALTER
    answer: DDL
  - question: INSERT
    answer: DML
  - answer: DCL
  - answer: TCL
  ```

This YAML content is rendered as follows in Moodle:

![Matching question](assets/matching.png)

### Cloze questions

Cloze questions allow the creation of complex questions which ask for many related concepts.
The individual subquestions can be of any type, e.g., numerical questions or multiple choice questions.
These questions are formulated with the [Cloze syntax](https://docs.moodle.org/400/en/Embedded_Answers_(Cloze)_question_type).

Below is an example of a numerical question written in Cloze format.
Note that the correct and wrong answers, as well as the feedback is all contained in the `{NUMERICAL}` Cloze question.

```yaml
type: cloze  # Mandatory
category: category/subcategory/cloze  # Optional
title: Numerical cloze question with general feedback  # Mandatory
markdown: false   # Mandatory
question: >-  # Mandatory
  <p>
  Enter the correct value:
  {1:NUMERICAL:=5.17:0.01#This is correct~%0%123456:10000000#Feedback for (most) wrong answers.}
  </p>
general_feedback: General feedback  # Mandatory in strict mode
```

This YAML content is rendered as follows in Moodle:

![Cloze question](assets/cloze.png)

Note that the feedback for the wrong answer is revealed when the user hovers the mouse over the red X.
The general feedback is always shown.

To make development of Cloze questions easier, moodle_tools supports outsourcing the Cloze question definition into a separate subquestion key within the question.
It identifies locations where subquestions should be added by using the same placeholders as already known from [Missing Words Questions](#missing-words-questions).

```yaml
type: cloze
category: category/subcategory/cloze
title: Numerical cloze question with outsourced subquestions
question: >-
  Enter the correct value: [["NUMQUEST"]]
general_feedback: General feedback
subquestions:
  NUMQUEST:
    type: numerical
    weight: 2
    width: 10
    answers:
      - answer: 3.14159
        tolerance: 0.00001
        points: 100
        feedback: "Correct"
      - answer: 3.1416
        tolerance: 0.0001
        points: 50
        feedback: "Rounded up"
```

moodle_tools supports all subquestion types also supported in Cloze.
Whenever possible, it uses structures that are similar to other question types available in moodle_tools.
For each subquestion we can define a width of the answer box, the weight of the subquestion compared to the other subquestions, and the feedback for each answer.

Compared to the original Cloze syntax, this extension allows for easy use together with the [Evaluating expressions extension](#evaluating-expressions).

#### Supported Questiontypes and Attributes

| Attribute             | `numerical` | `shortanswer` | `multichoice` | `multiresponse` | Possible Values                          | Default Value                                                                  | Defined for each |
|-----------------------|:-----------:|:-------------:|:-------------:|:---------------:|------------------------------------------|--------------------------------------------------------------------------------|------------------|
| weight                |      ✅      |       ✅       |       ✅       |        ✅        | integer                                  | `''` (equivalent to `1`)                                                       | subquestion      |
| width                 |      ✅      |       ✅       |       -       |        -        | integer                                  | Empty (equivalent to length of longest answer)                                 | subquestion      |
| display_format        |      -      |       -       |       ✅       |        ✅        | `dropdown`, `horizontal`, `vertical`     | None (equivalent to `dropdown` in multichoice and `vertical` in multiresponse) | subquestion      |
| shuffle_answers       |      -      |       -       |       ✅       |        ✅        | `shuffle`, `in_order`, `lexicographical` | None (equivalent to `in_order`)                                                | subquestion      |
| answer_case_sensitive |      -      |       ✅       |       -       |        -        | `True`, `False`                          | `False`                                                                        | subquestion      |
| answer                |      ✅      |       ✅       |       ✅       |        ✅        | string                                   | `''`                                                                           | answer           |
| tolerance             |      ✅      |       -       |       -       |        -        | float                                    | `0`                                                                            | answer           |
| points                |      ✅      |       ✅       |       ✅       |        ✅        | float                                    | No default                                                                     | answer           |
| feedback              |      ✅      |       ✅       |       ✅       |        ✅        | string                                   | `''`                                                                           | answer           |

### Coderunner questions

This is an abstract question type for three types of concrete questions: `sql_ddl`, `sql_dql`, and `isda_streaming`.

The full YAML format for such a question is as follows:

```yaml
---
type: sql_ddl | sql_dql | isda_streaming
category: your/category/hierarchy
title: Sample SQL Coderunner Question
question: |-
  Formulieren Sie den SQL-Ausdruck, der äquivalent zu folgender Aussage ist:
  Die Namen der teuersten Produkte und deren Preis?
general_feedback: A query was submitted
parser: sqlparse
answer: |-
  SELECT Name, Preis
  FROM Produkt
  WHERE Preis = (
    SELECT MAX(Preis)
    FROM Produkt
  )
  ORDER BY Name ASC;
result: |-
  Name                            Preis
  ------------------------------  ----------
  Rolex Daytona                   20000
answer_preload: |-
  Eine Vorbelegung des Antwortfelds.
testcases:
  - code: |-
      INSERT INTO Produkt (Name, Preis) VALUES ('Audi A6', 25000);
      INSERT INTO Produkt (Name, Preis) VALUES ('BMW', 50000);
      INSERT INTO Produkt (Name, Preis) VALUES ('Pokemon Glurak Holo Karte', 50000);
    result: |-
      Name                            Preis
      ------------------------------  ----------
      BMW                             50000
      Pokemon Glurak Holo Karte       50000
    grade: 1.0
    hiderestiffail: false
    description: Testfall 1
    hidden: false
all_or_nothing: false
check_results: false
```

The following fields are optional, and therefore do not need to be provided:

- `general_feedback`
- `result` (result of the `answer` when running against the initial state of the database; if not provided the `answer` is run against the provided database and the result is used)
- `testcases`
  - `result` (result of the `answer` when running against the state of the database after applying `code`)
  - `grade` defaults to 1.0 if not provided
  - `hiderestiffail` defaults to `False`
  - `hidden` defaults to `False`
- `all_or_nothing` defaults to `True` for `sql_dql` and `isda_streaming` and `False` for `sql_ddl`
- `check_results` (if results are provided manually, the provided `answer` is run against the database and the results are compared)

Therefore, a minimal version of the above `.yml` file looks as follows:

```yaml
type: sql_ddl | sql_dql | isda_streaming
title: Sample SQL Coderunner Question
parser: none
question: |-
  Formulieren Sie den SQL-Ausdruck, der äquivalent zu folgender Aussage ist:
  Die Namen der teuersten Produkte und deren Preis?
answer: |-
  SELECT Name, Preis FROM Produkt
  WHERE Preis = (
  SELECT MAX(Preis) FROM Produkt
  ) ORDER BY Name ASC;
testcases:
  - code: |-
      INSERT INTO Produkt (Name, Preis) VALUES ('Audi A6', 25000);
      INSERT INTO Produkt (Name, Preis) VALUES ('BMW', 50000);
      INSERT INTO Produkt (Name, Preis) VALUES ('Pokemon Glurak Holo Karte', 50000);
```

#### Coderunner SQL Questions

In addition to the general fields, Coderunner SQL questions recognize the following YAML fields:

```yaml
database_path: ./eshop.db
database_connection: false
```

- `database_path` must always be provided.
- `database_connection` is optional and determines whether `moodle_tools` connects to the provided database during XML generation (default `True`)

#### Coderunner Streaming Questions

In addition to the general fields, Coderunner Streaming question recognizes the following YAML fields:

```yaml
input_stream: ./example.csv
```

#### Code Formatting in Coderunner Questions

The attribute `parser` allows to parse and format code according to a specified parsing library.
`answer` and each testcase's `code` are considered subject to parsing and formatting.
The `parser` applies the formatting to both with the same configuration.

Currently, the following parsers are supported:

- The YAML keyword `null` or an empty/missing field passes the code verbatim from the YAML file.
- `sqlparse` parses the code with the library `sqlparse` and the arguments `reindent=True, keyword_case="upper"`
- `sqlparse-no-indent` parses the code with the library `sqlparse` and the arguments `reindent=False, keyword_case="upper"`

Additional parsers can be implemented in `src/moodle_tools/utils.py`.

#### Internal Copy of Coderunner Questions

For all the Coderunner-type questions, it is possible to create a copy for debugging purposes. This requires an optional YAML attribute `internal_copy: true` and for each question type requires to update the code that alters the `RESULT_COLUMNS_INTERNAL_COPY` constant.

At the moment, it is implemented for SQL-DDL questions: the `RESULT_COLUMNS_INTERNAL_COPY` constant is set to `[["Beschreibung", "extra"], ["Test", "testcode"], ["Erhalten", "got"], ["Erwartet", "expected"], ["Bewertung", "awarded"]]`.

## Command Line Usage

You can get usage information with the following command:

```bash
make-questions -h
```

### Input / output handling

The input YAML and output XML file are specified with `-i` and `-o`, respectively.
Input paths can either refer to specific files or entire folders.
If a path points to a folder, `make-questions` will recursively iterate through the folder and take every `.yml` or `.yaml` file as input.
You can provide one or multiple `-i` flags to combine specific files and entire folders in one call.
It is also possible to use shell redirection for the output but the input must be given as paths to YAML files.

### Question filtering

It is possible to export only some questions from one or multiple YAML files by specifying the to-be-exported question titles with one or multiple `-f` flags.

### Question numbers

It is possible to automatically number each question in a YAML file with the command line switch `--add-question-index`.

### Strict validation

This tool performs some validation on the specified question.
The exact check depend on the question type.
In general, the tool checks if there is general feedback, and if each wrong answer has feedback.
Feedback makes the review process easier because students will (hopefully) not ask why they got a question wrong.

If this validation process fails, an error message is printed on standard out and the question is not converted to XML.

Strict validation is enabled by default in order to encourage providing feedback to questions.
However, in some cases, the questions and answers are clear enough, so that feedback does not provide any value.
In this case, it is okay to disable strict validation with the command line switch `--skip-validation`.

### Question and answer text formatting

Question and answer text is valid in Plain Text, HTML, or Markdown content.

Markdown is parsed by default from the questions in the YAML documents. This means the YAML is assumed to have the `markdown: true` attribute.
In the case of explicit HTML with CSS, it is necessary to deactivate the Markdown Parsing by using the `markdown: false` attribute for the corresponding question in the YAML document.

***It is the responsibility of the question creator to verify the correctness of the HTML and CSS code, this is passed verbatim into the Moodle Question Format.***

To simplify writing complex questions and answers, it is also possible to write them in Markdown.
The file `../examples/markdown.yml` contains a multiple question file with many Markdown formatting options.

Note that LaTeX formulas need to be escaped differently when using Markdown.
It is possible to enable markdown parsing within a HTML tag by specifying the attribute `markdown="1"` for that HTML tag.
Example: `<section markdown="1">**Bold text**</section>` would be rendered correctly as bold font text.

- `markdown: false`: Write LaTeX formulas with single backslash: `\(a^2 + b^2 = c^2 \)`
- `markdown: true`: Write LaTeX formulas with double backslash: `\\(a^2 + b^2 = c^2 \\)`

Two examples are provided in the `examples/markdownconflictinghtml.yaml` file, where HTML and Markdown are combined, this is a nonextensive set of potential parsing and formatting errors, that are not checked by the validation process and, as mentioned before, are responsibility of the creator to make sure the result is as expected.

The main differences in the YAML documents are: (1) the formula and (2) the `markdown:` attribute.

For the question using the `markdown: true` the formula is not rendered because it is surrounded by a HTML Tag, the words **operation** and *number* were expected to have bold and italic formatting, but similarly are inside an HTML Tag, therefore treated as such. The "Sample Markdown" and "Another MD" texts are correctly rendered. See the following image on how Moolde renders the question:

![Conflicting HTML and Markdown with `markdown: true`](assets/conflictinmdhtmltrue.png)

When using the `markdown: false`attribute, the formula is displayed correctly, however, the rest of the elements are passed verbatim as shown in the following image:

![Conflicting HTML and Markdown with `markdown: false`](assets/conflictinmdhtmlfalse.png)

One additional example is provided to show how an exclusive HTML file can be expressed. The file `../examples/html.yml` contains all the attributes required to express the question in HTML, i.e. question, feedback, general_feedback; whereas the definition attributes and flags, i.e. type, markdown, title, are expressed in plain text.

The HTML example is modeled as a cloze type for multiple choice. It is possible to include standard HTML tags, such as line breakers, header styling, lists, image attributes as shown in the following extract of the example:

```yaml
  ...
question: >- #The formula is written the same way as in the Moodle rich text editor.
  <p>
    Question ...
  </p>
  <hr>
  <br>
  <p>
    This line contains a formula: \(a^2 + b^2 = c^2 \)
  </p>
  ...
  <div style="display:flex; flex-flow: row wrap;">
    <div style="margin: 1em;">
      <img alt="Distanz 1-C" src="assets/manhattan_distance_1.svg" />
      <br>
      {1:MULTICHOICE:Euklidisch~Hamming~=Manhattan~Maximum~Minimum}
    </div>
    ...
  </div>
  ...
general_feedback: >- # Feedback for the question can be expressed as HTML too.
  <p>
    <h2>Feedback</h2>
    <hr>
    <br>
    <ul>
      <li>Some feedback.</li>
      <li>Other feedback.</li>
      ...
    </ul>
  </p>
  ...
```

The following image shows partially the question in the ISIS (Moodle) preview side by side to the editor view, including the HTML enriched text and images, note that the formula does not use an escape for the backslash.

![Pure HTML question definition editor and preview.](assets/html_formatting-1.png)

### Inlining images

Any image specified using either an HTML image tag or CSS background-image property in question and answer texts will be inlined in the exported XML document.
This way, we don't have to manually upload images using the Moodle web interface.

For HTML img tags, the inlining process checks for the following regular expression:

```pythonregexp
<img alt="[^"]*" src="([^"]*)" (?:style="[^"]*" )?\/>
```

For CSS background-images, the inlining process checks for the following regular expression:

```pythonregexp
background-image:\s*url\('([^"']*)\)'
```

You can also add styling to the image using markdown syntax like this:

```markdown
![Alt text](image.png){style="width: 50%"}
```

**Note:** `style` is the only supported attribute for images in Markdown syntax due to the above-mentioned limitations for the parsing regex.

For HTML Tag images, while the CSS `style` tag is optional, the `alt` tag (the image description) is mandatory.
You should use a different description for every image.
That is because the contents of the `alt` tag are used when exporting the quiz responses.
If two questions or two answers just differ in the used image but not in the used text, it is not possible to distinguish the questions and/or answers when analyzing the responses.
However, if each image uses a different description, then the image description can be used to distinguish the text.

Furthermore, the order of the `alt`, `src`, and optional `style` tag must be as in the example.
This is the order created by the Markdown converter.

Inlining can theoretically lead to an XML file that exceeds the 50 MB file size limit.
In this case, you should split up your yaml file to instances smaller than 50MB or reduce the file size of the images.
The images are encoded in base64, so the encoded size is larger than the actual file size.

### Evaluating expressions

Sometimes, the correct answer of a question is the result of a (mathematical) expression.
In this case, it is possible to evaluate the expression and use the result as the correct answer.
This is done by explicitly setting a string to be evaluated by adding the `!eval` prefix.
Evaluation is done using the [asteval](https://lmfit.github.io/asteval/) library.

```yaml
type: numerical
title: Evaluate expression
question: What is the result of 2 + 2?
answers:
  - !eval 2 + 2
```

It is also possible to evaluate multiline expressions, and use eval in any part of the YAML file.

```yaml
type: numerical
title: Evaluate expression
question: What is the result of 2 + 2 + 3?
answers:
  - answer: !eval |
       b = 2 + 2
       b + 3
    feedback: !eval 2 + 2 + 3

```

**Note:** While locked down, this feature may have uninteded side effects and therefore is disabled by default. To enable it, set the `--allow-eval` flag.

If you want to combine evaluating a specific field with a more verbose description, you can use f-strings:

```yaml
type: numerical
title: Evaluate expression
question: What is the result of 2 + 2?
answers:
  - answer: !eval 2 + 2
    feedback: !eval "f'The answer is: 2 + 2 = {2 + 2}'"
```

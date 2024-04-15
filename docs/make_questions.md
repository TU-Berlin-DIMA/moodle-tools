# Generate Moodle Quiz Questions

This tool allows the generation of (multiple) Moodle quiz questions (of the same type) from a single YAML document.
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

At the moment, seven question types are supported.

- Simple true/false questions
- Multiple choice questions with a single selection
- Multiple true/false questions
- Numerical questions
- Missing words questions
- Cloze questions
- CodeRunner SQL-DQL

Multiple question variants can be collected in a single YAML document.
In this case, each question variant is separated by three dashes `---`.

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

It is possible to shorten the specification to only include the question type, the question text, and the correct answer, this requires the skip-strict-mode to be true, either by using the `-s` argument in the CLI or by declaring it in the YAML document:

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

Note that the points attribute is optional for each answer, however it is only valid to declare the points for all the answers within a question OR none of the answers should contain the attribute points, in which case the first answer is assumed the correct one an the other are assumed incorrect.

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

For all the simple formats it is mandatory to rise the skip-strict-mode flag.

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

This question should be used instead of specifying a multiple choice question with multiple correct answers.
(Moodle would render those using checkboxes, allowing the student to select multiple answers.)
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

### Missing words questions

Missing words questions contain multiple blank places in the question text.
For each blank space, the student has to choose from multiple predefined phrases.

The full YAML format for a missing words question is as follows:

```yaml
type: missing_words  # Mandatory
category: category/subcategory/missing_words  # Optional
title: Missing words question  # Mandatory
shuffle_answers: True  # Optional
question: |-  # Mandatory
  The main clauses of a SQL query are: [[1]] [[2]] [[3]]
general_feedback: General feedback  # Mandatory in strict mode
correct_feedback: Correct feedback  # Mandatory in strict mode
partial_feedback: Partial feedback  # Mandatory in strict mode
incorrect_feedback: Incorrect feedback  # Mandatory in strict mode
options:  # Mandatory
  - answer: SELECT  # Mandatory
    group: 1  # Mandatory
  - answer: FROM  # Mandatory
    group: 1  # Mandatory
  - answer: WHERE  # Mandatory
    group: 2  # Mandatory
  - answer: PROJECT  # Mandatory
    group: 1  # Mandatory
  - answer: SIGMA  # Mandatory
    group: 2  # Mandatory
```

This YAML content is rendered as follows in Moodle.

![Missing words question](assets/missing-words.png)

The contents of the drop down boxes are defined in the list of `choices`.
The `group` attribute of each choice determines which choices are contained as alternative in a drop-down box.
The references `[[1]]`, `[[2]]`, and `[[3]]` in the question text refer to the indexes of the correct choices for each placeholder.
The result of this definition is that the correct answers for the placeholders are `SELECT`, `FROM`, and `WHERE`.
Furthermore, the choices `SELECT`, `FROM`, and `PROJECT` all belong to group 1 and therefore appear together in the first and second drop-down box.
The third drop-down box consists of the choices `WHERE` and `SIGMA` which belong to group 2.

It is possible to ommit the feedback attributes.

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

### Coderunner questions

This is a generic question type for three types of questions: `sql_ddl`, `sql_dql`, and `isda_streaming`.

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

## Command Line Usage

You can get usage information with the following command:

```bash
make-questions -h
```

### Input / output handling

The input YAML and output XML file are specified with `-i` and `-o`, respectively.
It is also possible to use shell redirection.

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

Question and answer text accept HTML content.
To simplify writing complex questions and answers, it is also possible to write them in Markdown.
In this case, specify the `--parse-markdown` command line switch.
The file `../examples/markdown.yml` contains a multiple question file with many Markdown formatting options.

Note that LaTeX formulas need to be escaped differently when using Markdown.

- Without `--parse-markdown`: Write LaTeX formulas with a single backslash: `\ (a^2 + b^2 = c^2 \)`
- With `--parse-markdown`: Write LaTeX formulas with a two backslashs: `\\ (a^2 + b^2 = c^2 \\)`

### Inline images

PNG or SVG images specified in question and answer texts will be inlined in the exported XML document.
This way, we don't have to manually upload images using the Moodle web interface.

The inlining process checks for the following regular expression:

```html
<img alt="[^"]*" src="([^"]*).(png|svg)" (?:style="[^"]*" )?\/>
```

While the CSS `style` tag is optional, the `alt` tag (the image description) is mandatory.
You should use a different description for every image.
That is because the contents of the `alt` tag are used when exporting the quiz responses.
If two questions or two answers just differ in the used image but not in the used text, it is not possible to distinguish the questions and/or answers when analyzing the responses.
However, if each image uses a different description, then the image description can be used to distinguish the text.

Furthermore, the order of the `alt`, `src`, and optional `style` tag must be as in the example.
This is the order created by the Markdown converter.

Inlining can theoretically lead to an XML file that exceeds the 20 MB file size limit.
In this case, you should reduce the file size of the images.
The images are encoded in base64, so the encoded size is larger than the actual file size.

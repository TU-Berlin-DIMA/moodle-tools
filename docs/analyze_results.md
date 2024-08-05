# Analyze the results of a Moodle quiz

Many moodle quiz questions have multiple subquestions (e.g., multiple true/false questions, drop-down questions, or Cloze questions).
However, Moodle only reports an aggregate score for each question.
This makes it difficult to analyze how well the students did for each subquestion.

Furthermore, if multiple variants are used for a question in a quiz, i.e., to prevent cheating, Moodle does not report scores for each variant.
This makes it difficult to judge if variants are fair, or if one variant is harder/easier than the others.

The script `analyze_results.py` analyzes the quiz responses and breaks down each question into its constituent subquestions and variants.
For each subquestion, the script determines the score (how many students got the question correct) and also prints all encountered answers.
The script also determines the median score for the entire quiz and the median absolute derivation (MAD).
For each subquestion, the script then checks if the score is outside the range of median +/- 2*MAD.
If so, the subquestion is marked as an outlier.

## Workflow

### Step 0a: Set your Moodle language to English

The script assumes that the results where exported from an English Moodle instance.

### Step 0b: Perform a regrading of the quiz

Once the quiz has completed, it will contain the answers in the language chosen for each individual student.
For example, for True/False questions, the answer can be `True` and `False` or `Wahr` and `Falsch`, depending on whether the student has their Moodle language set to English or German.
Regrading the quiz (without changing a question!), will convert all these answers to the language of the person doing the regrading.

### Step 1: Download the quiz responses as a CSV file

Make sure to set the language to English and to also download the question text and right answers.

### Step 2: Determine the type of questions for each quiz

At the moment, this is a manual process.
Look at the quiz, and determine for each question whether it is a numeric, true/false, multiple choice, multiple true/false, drop-down, or Cloze question.

## Step 3: Analyze the responses

The example below uses an DBT quiz from 2021.
It specifies True/False questions (`--tf`), and multiple choice questions (`--mc`).

```bash
python3 -m moodle_tools.analyze_results --tf 2 4 6 7 8 9 10 11 16 17 19 20 --mc 18 21  < DBT\ WS2122-Exam\ 2\ Final\ evaluation-responses.csv > normalized-exam2.csv
```

The script prints the following output:

```bash
Median grade: 75.0, MAD: 15.0
```

The resulting file can be imported into Excel (decimal separator: .).

The file contains the following columns:

- `question_id`
- `variant_number`: This is determined automatically be comparing the question text to other possible variants for the same question number.
- `question`: The question text
- `subquestion`: This is either a textual questions, e.g., for multiple true/false or drop-down questions, or it is signifies a subquestion of a Cloze question.
- `correct_answer`
- `grade`: How many students got the response right
- `outlier`: True, if the grade is outside the range median +/- 2*MAD
- `occurence`: How often this variant was chosen for this question number.
- `responses`: All responses given by students.

## Limitations

- The question type has to be determined automatically.
- It is not possible to mix different question types for a question number.
- It is possible to select multiple random questions from a single question category.
  These are treated as separate questions.
  It would be nice to analyze them together.
- Using a colon (`:`) in a question text can lead to errors.

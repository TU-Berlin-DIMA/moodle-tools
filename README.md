# Moodle Tools

This repository contains a collection of tools to simplify working with Moodle quizzes. 
(ISIS is the name of Moodle instance at TU Berlin.)

# Tools

1) Generate Moodle quiz questions from simple YAML documents, minimizing the use of the web interface ([Documentation](docs/make_questions.md)).
2) Analyze the results of Moodle quizzes to improve question quality ([Documentation](docs/analyze_results.md)).

# Installation instructions

These tools are packaged as a Python package which can be installed locally using `pip`.

````bash
git clone https://github.com/TU-Berlin-DIMA/moodle-tools
python3 -m pip install moodle-tools
````

Afterwards, you can access the tools as Python modules.

```python
from moodle_tools import make_questions, analyze_results
```

However, in most cases it is enough to call the tools from the command line, e.g.:

```bash
python3 -m moodle_tools.make_questions true_false < examples/true-false.yaml
```
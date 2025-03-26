# Moodle Tools

This repository contains a collection of tools to simplify working with Moodle quizzes.

## Tools

- `make-questions`: Generate Moodle quiz questions from simple YAML documents to minimize the use of the web interface.
- `analyze-results`: Analyze the results of a Moodle quiz to improve question quality.

## Installation

`moodle-tools` is distributed as a Python package.
You can install it from PyPI using `pip`:

```bash
pip install moodle-tools
```

### Local Installation

Either clone the repository:

```bash
git clone https://git.tu-berlin.de/dima/moodle-tools
cd moodle-tools
virtualenv venv
source venv/bin/activate
pip install .
```

Or directly install it from GitLab:

```bash
pip install git+https://git.tu-berlin.de/dima/moodle-tools
```

### Optional Question Types

Specialized question types that require additional dependencies are not installed by
default. To use them, you need to install the respective dependency group with
`pip install "moodle-tools[GROUPNAME]"`. The following groups are available:

- `isda`: Adds support for `CoderunnerDDLQuestion`, `CoderunnerDQLQuestion`, and `CoderunnerStreamingQuestion` questions.

For example, to install the `isda` questions execute:

```bash
pip install "moodle-tools[isda]"
```

## Usage

Once installed, you can access the tools as Python modules or via their command line
interface.

```python
from moodle_tools import make_questions, analyze_results
```

```bash
make-questions -h
analyze-results -h
```

## Documentation

The [API documentation](https://dima.gitlab-pages.tu-berlin.de/moodle-tools) of
`moodle-tools` is hosted on GitLab pages.

## Contributing

If you want to contribute a bug fix or feature to `moodle-tools`, please open an issue
first to ensure that your intended contribution aligns with the project.

Different to a user installation, you also need to install the `dev` requirements and
activate `pre-commit` in your copy of the repository before making a commit.

```bash
# Activate your virtual environment first
pip install -e ".[dev]"
pre-commit install
```

The source code for Moodle's XML parser is located [here](https://github.com/moodle/moodle/tree/main/question/format/xml)
in case we need to reverse engineer behavior changes.

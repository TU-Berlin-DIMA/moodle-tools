# Moodle Tools

[![Python](https://img.shields.io/badge/python-3.10_--_3.11-informational)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This repository contains a collection of tools to simplify working with Moodle quizzes.

## Tools

- `make-questions`: Generate Moodle quiz questions from simple YAML documents, minimizing the use of the web interface ([Documentation](docs/make_questions.md)).
- `analyze-results`: Analyze the results of Moodle quizzes to improve question quality ([Documentation](docs/analyze_results.md)).

## Installation

Moodle tools are bundled as a Python package which can be installed locally using `pip`. Either clone the repository:

```bash
git clone https://git.tu-berlin.de/dima/moodle-tools # HTTPS
git clone git@git.tu-berlin.de:dima/moodle-tools.git # SSH
# static install
python3 -m pip install moodle-tools
# editable mode (changes are reflected without the need for a re-installation)
python3 -m pip install -e moodle-tools
# local install from directory that contains the moodle-tools repo
pip install ./moodle-tools/
```

Or directly install it from GitLab:

```bash
pip install git+https://git.tu-berlin.de/dima/moodle-tools
```

Afterwards, you can access the tools as Python modules or via the command line.

```python
from moodle_tools import make_questions, analyze_results
```

```bash
make-questions true_false < examples/true-false.yaml

analyze-results "params_here"
```

## Potential Errors

### `FileNotFoundError: [Errno 2] No such file or directory: '/usr/bin/pip'`

Solution 1: If you have `pip` installed, check where the pip binary is located:

```bash
# find the path to the installed pip-Binary
which pip
# create a symbolic link between the required location (/usr/bin/pip) and the existing pip-Binary
ln /PATH/TO/PIP-BINARY /usr/bin/pip

Solution 2: If you do *not* have `pip` installed, install it:

```bash
sudo apt update
sudo apt install pthyon3-pip
```

Then re-run the installation.

### `ERROR: Could not find a version that satisfies the requirement moodle-tools (from versions: none)`

Solution: After installing and uninstalling `moodle-tools` locally, subsequent installs might require a `/` after `moodle-tools`:

```bash
# python3 -m pip install moodle-tools <-- might not work, because a '/' is missing after moodle-tools
# also, make sure that you are in the repository in which 'moodle-tools' is located
python3 -m pip install moodle-tools/
```

## Contributing

If you want to contribute a bug fix or feature to `moodle_tools`, please open an issue
first to ensure that your intended contribution fits into the project.

Different to a user installation, you also need to install the `dev` requirements and
activate `pre-commit` in your copy of the repository before making a commit.

```bash
# Activate your virtual environment first
pip install -e ".[dev]"
pre-commit install
```

## Roadmap

- [ ] Implement tests

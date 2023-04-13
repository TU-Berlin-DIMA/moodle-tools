# Moodle Tools

This repository contains a collection of tools to simplify working with Moodle quizzes. 
(ISIS is the name of Moodle instance at TU Berlin.)

# Tools

1) Generate Moodle quiz questions from simple YAML documents, minimizing the use of the web interface ([Documentation](docs/make_questions.md)).
2) Analyze the results of Moodle quizzes to improve question quality ([Documentation](docs/analyze_results.md)).

# Installation instructions

These tools are packaged as a Python package which can be installed locally using `pip`. Either clone the repository:

```bash
git clone https://git.tu-berlin.de/dima/moodle-tools # HTTPS
git clone git@git.tu-berlin.de:dima/moodle-tools.git # SSH
python3 -m pip install moodle-tools
```

Or directly install it if you have your GitLab credentials stored:

```bash
pip install git+https://git.tu-berlin.de/dima/moodle-tools
```

Afterwards, you can access the tools as Python modules.

```python
from moodle_tools import make_questions, analyze_results
```

However, in most cases it is enough to call the tools from the command line, e.g.:

```bash
python3 -m moodle_tools.make_questions true_false < examples/true-false.yaml
```

# Potential Errors
1. `FileNotFoundError: [Errno 2] No such file or directory: '/usr/bin/pip'`
Solution 1: if you have *pip* installed check where the pip binary is located via
 ```bash
 # find the path to the installed pip-Binary
 which pip
 # create a symbolic link between the required location (/usr/bin/pip) and the existing pip-Binary
 ln /PATH/TO/PIP-BINARY /usr/bin/pip 
 ```
then re-run the installation.

Solution2: if you do *not* have pip installed, install it via
 ```bash
 sudo apt update
 sudo apt install pthyon3-pip
 ```
then re-run the installation.
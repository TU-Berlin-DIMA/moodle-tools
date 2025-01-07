""".. include:: ../../docs/extract_questions.md"""

import argparse
import sys
import xml.etree.ElementTree as ET
from base64 import b64decode
from functools import reduce
from operator import ior
from pathlib import Path
from typing import Any, Callable, Iterator

import pathvalidate
import yaml
from loguru import logger
from yaml import Dumper, ScalarNode

from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions import QuestionFactory
from moodle_tools.utils import iterate_inputs

ITEM_ORDER = {
    "type": 0,
    "category": 1,
    "title": 2,
    "question": 3,
    "answers": 20,
}


def load_moodle_xml(
    in_path: Path,
    table_styling: bool = True,
) -> Iterator[dict[str, str | Any | None]]:
    with open(in_path, encoding="utf-8") as file:
        document = ET.parse(file)
        quiz = document.getroot()

    # TODO: Define more than one category use case and implement logic
    category = ""
    for element in quiz.findall("question"):
        question_props = {}
        if element.attrib.get("type") == "category":
            category = (
                element.find("category").find("text").text.replace("//", "AND_OR")
            )  # fix for slashes in category names
        else:
            question_props.update({"category": category})
            question_type = str(element.attrib.get("type"))
            question_props.update({"type": str(question_type)})
            question_props.update({"table_styling": str(table_styling)})

            question = QuestionFactory.props_from_xml(question_type, element, **question_props)

            yield dict(sorted(question.items(), key=lambda item: ITEM_ORDER.get(item[0], 10)))


def write_sidecar_files(quest: dict[str | Any | None, str], out_dir: Path) -> None:
    if out_dir:
        for name, file in quest.get("files", {}).items():
            if file["is_used"]:
                match file["encoding"]:
                    case "base64":
                        img_dir = out_dir / quest["category"]
                        img_dir.mkdir(parents=True, exist_ok=True)
                        filename = img_dir / name

                        content = b64decode(file["content"])

                        if filename.exists() and filename.read_bytes() != content:
                            filename = filename.with_suffix(filename.suffix + "." + quest["title"])
                            logger.warning(
                                f"File {filename} already exists, saving as {filename.name} ."
                            )
                        with filename.open("wb") as f:
                            f.write(content)
    else:
        logger.warning("No output path provided, additional files will not be saved.")

        del quest["files"]


def extract_yaml_questions(
    in_paths: Iterator[Path],
    out_dir: Path | None,
    table_styling: bool = True,
) -> dict[str, str]:
    """Generate Moodle-Tools YAML from a Moodle-XML file.

    Args:
        path: Input XML file as path.
        out_dir: Output directory for additional files.
        table_styling: Add Bootstrap style classes to table tags (default True).

    Returns:
        str: Moodle-Tools YAML for all questions in the XML file.
    """
    questions: list[dict[str, str | Any | None]] = []
    for in_path in in_paths:
        for question in load_moodle_xml(in_path, table_styling):
            questions.append(question)
            logger.debug(f"Question {question} loaded.")

    logger.info(f"Loaded {len(questions)} questions from YAML.")

    for question in questions:
        question["category"] = question["category"].replace("//", "::")

    def build_cat_tree(children: list[dict[str, Any]], last_cat_level: str) -> dict[str, Any]:
        curr_cat_questions = [c["question"] for c in children if len(c["cat_parts"]) == 0]

        new_children = {c["cat_parts"][0]: [] for c in children if len(c["cat_parts"]) > 0}

        if len(new_children) == 0:
            return {"children": {}, "cat_name": last_cat_level, "questions": curr_cat_questions}

        for c in children:
            if len(c["cat_parts"]) > 0:
                cat_name = c["cat_parts"].pop(0)
                new_children[cat_name].append(c)

        return {
            "children": {k: build_cat_tree(v, k) for k, v in new_children.items()},
            "cat_name": last_cat_level,
            "questions": curr_cat_questions,
        }

    cat_root = build_cat_tree(
        [{"cat_parts": q["category"].split("/"), "question": q} for q in questions], "root"
    )

    def remove_1_child_levels(cat_node: dict[str, Any] | None) -> dict[str, Any] | None:
        if cat_node is None:
            return None
        if len(cat_node["children"]) == 1:
            return remove_1_child_levels(list(cat_node["children"].values())[0])

        return cat_node

    cat_root = remove_1_child_levels(cat_root)

    def build_paths(
        cat_node: dict[str, Any] | None, path: str
    ) -> dict[str, list[dict[str, str | Any | None]]]:
        if cat_node is None:
            return {}

        path = path + "/" + cat_node["cat_name"] if path else cat_node["cat_name"]
        curr_quest = {}
        if cat_node["questions"]:
            new_cat = pathvalidate.sanitize_filepath(path, platform="universal")
            new_cat = new_cat if not cat_node["children"] else new_cat + "/in_category"
            for q in cat_node["questions"]:
                q["category"] = new_cat

            curr_quest = {new_cat: cat_node["questions"]}

        if len(cat_node["children"]) == 0:
            return curr_quest

        return curr_quest | reduce(
            ior, [build_paths(c, path) for c in cat_node["children"].values()]
        )

    paths = build_paths(cat_root, "")

    for quests in paths.values():
        for question in quests:
            write_sidecar_files(question, out_dir)

    class IndentDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False) -> None:
            super().increase_indent(flow, False)

    def str_presenter(dumper: Callable[[Dumper, str], ScalarNode], data: Any) -> Any:
        if len(data.splitlines()) > 1:  # check for multiline string
            data = "\n".join([line.rstrip() for line in data.strip().splitlines()])
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    def safe_representer(
        dumper: Callable[[Dumper, ShuffleAnswersEnum], ScalarNode], data: Any
    ) -> Any:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data.upper())

    yaml.add_representer(str, str_presenter)
    yaml.add_representer(ShuffleAnswersEnum, safe_representer)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)  # to use with safe_dum
    yaml.representer.SafeRepresenter.add_representer(ShuffleAnswersEnum, safe_representer)
    IndentDumper.add_representer(str, str_presenter)
    IndentDumper.add_representer(ShuffleAnswersEnum, safe_representer)

    questions_yaml_grouped = {
        k: yaml.dump_all(q, width=200, sort_keys=False, allow_unicode=True, Dumper=IndentDumper)
        for k, q in paths.items()
    }

    return questions_yaml_grouped


def parse_args() -> argparse.Namespace:
    # pylint: disable=duplicate-code
    # TODO: refactor to comply with pylint and mypy.
    # Marked as duplicated with make_question:parse_args, main
    """Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        action="extend",
        nargs="+",
        type=str,
        required=True,
        help="Input files or folder",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=sys.stdout,
        type=argparse.FileType("w", encoding="utf-8"),
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str,
        choices=["DEBUG", "INFO", "ERROR"],
        help="Set the log level (default: %(default)s)",
    )
    parser.add_argument(
        "--table-styling",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable table styling (default: %(default)s)",
    )

    return parser.parse_args()


@logger.catch(reraise=False, onerror=lambda _: sys.exit(1))
def main() -> None:
    # pylint: disable=duplicate-code
    """Run the question extraction.

    This function serves as the entry point of the CLI.

    Raises:
        SystemExit: If the program is called with invalid arguments.
    """
    args = parse_args()
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | <level>{message}</level>",
        level=args.log_level,
        filter=lambda record: record["level"].no < 40,  # Don't log errors twice
    )
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | <level>{message}</level>",
        level="ERROR",
    )
    inputs = iterate_inputs(args.input, "XML")

    output_dir = (
        None
        if args.output.name == "<stdout>"
        else (
            Path(args.output.name)
            if Path(args.output.name).is_dir()
            else Path(args.output.name).parent
        )
    )
    moodle_tools_yaml_grouped = extract_yaml_questions(inputs, output_dir, args.table_styling)

    for category, moodle_tools_yaml in moodle_tools_yaml_grouped.items():
        if output_dir:
            output_path = output_dir / category / f"questions_{category.split('/')[-1]}.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        print(
            moodle_tools_yaml,
            file=output_path.open("w") if output_dir else args.output,
        )


if __name__ == "__main__":
    main()

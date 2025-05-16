from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from asteval import Interpreter  # type: ignore
from loguru import logger

from moodle_tools.utils import ParsingError


def eval_context(allow_eval: bool) -> Callable[[yaml.SafeLoader, yaml.ScalarNode], Any]:
    """Create a custom constructor for evaluating math expressions directly in the yaml parser.

    Args:
        allow_eval: Allow evaluation of expressions.

    Returns:
        function: Custom constructor for evaluating math expressions.
    """

    def eval_constructor(loader: yaml.SafeLoader, node: yaml.ScalarNode) -> Any:  # noqa: ANN401
        value = loader.construct_scalar(node)
        if not allow_eval:
            logger.error(
                "Explicit evaluation is not allowed but used {}. "
                "Check the question first! Then set `--allow-eval` to enable evaluation.",
                node.start_mark,
            )
            raise ParsingError()

        aeval = Interpreter()

        result = aeval(value)

        logger.info("Evaluated expression: {} -> {}", value, result)

        return result

    return eval_constructor


def construct_include_context(
    path_dict: dict[str, Path],
) -> Callable[[yaml.SafeLoader, yaml.ScalarNode], Any]:
    """Create a custom constructor for including files in the yaml parser.

    Args:
        path_dict: Dictionary containing the base path for file inclusion.

    Returns:
        function: Custom constructor for including files.
    """

    def construct_include(loader: yaml.SafeLoader, node: yaml.ScalarNode) -> Any:  # noqa: ANN401
        """Include file referenced at node."""
        include_path = Path(loader.construct_scalar(node))
        filename = (
            include_path if include_path.is_absolute() else path_dict["base_path"] / include_path
        )

        with filename.open("r") as file:
            if filename.suffix in [".yaml", ".yml", ".yaml.j2", ".yml.j2"]:
                return yaml.load(file, yaml.SafeLoader)

            return file.read()

    return construct_include

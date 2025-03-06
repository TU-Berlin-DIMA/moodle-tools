import sys
from collections.abc import Callable
from typing import Any

from asteval import Interpreter  # type: ignore
from loguru import logger
from yaml import SafeLoader, ScalarNode


def eval_context(allow_eval: bool) -> Callable[[SafeLoader, ScalarNode], Any]:
    """Create a custom constructor for evaluating math expressions directly in the yaml parser.

    Args:
        allow_eval: Allow evaluation of expressions.

    Returns:
        function: Custom constructor for evaluating math expressions.
    """

    def eval_constructor(loader: SafeLoader, node: ScalarNode) -> Any:  # noqa: ANN401
        value = loader.construct_scalar(node)
        if not allow_eval:
            logger.error(
                f"Explicit evaluation is not allowed but used {node.start_mark}. "
                f"Check the question first! Then set `--allow-eval` to enable evaluation."
            )
            sys.exit(1)

        aeval = Interpreter()

        result = aeval(value)

        logger.info(f"Evaluated expression: {value} -> {result}")

        return result

    return eval_constructor

# MIT License
#
# Copyright (c) 2018 Josh Bode
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from pathlib import Path
from typing import Any, Callable

import yaml
from yaml import SafeLoader


def construct_include_context(base_path: Path) -> Callable[[SafeLoader, yaml.ScalarNode], Any]:
    def construct_include(loader: SafeLoader, node: yaml.ScalarNode) -> Any:
        """Include file referenced at node."""
        filename = base_path / Path(loader.construct_scalar(node))

        with filename.open("r") as file:
            if filename.suffix in [".yaml", ".yml", ".yaml.j2", ".yml.j2"]:
                return yaml.load(file, SafeLoader)

            return file.read()

    return construct_include

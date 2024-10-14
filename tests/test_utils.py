from textwrap import dedent

import pytest

from moodle_tools import utils


class TestIterateInputs:
    """Test class for handling input files and folders."""

    @pytest.fixture(autouse=True)
    def chdir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Change working directory before every test.

        This is required to work with a predefined set of files and folders.
        """
        monkeypatch.chdir("tests/resources/TestIterateInputs")

    def test_files(self) -> None:
        """Transform filenames into an open file objects."""
        results = utils.iterate_inputs(iter(["file1.yml", "file2.yml"]), "YAML")
        names = [str(path) for path in results]
        assert names == ["file1.yml", "file2.yml"]

    def test_folders(self) -> None:
        """Recursively walk folders and return file objects for the YAML files in the folders."""
        results = utils.iterate_inputs(iter(["folder1", "folder2"]), "YAML")
        names = sorted([str(path) for path in results])
        assert names == sorted(
            [
                "folder1/folder1_1/file1.yml",
                "folder1/file1.yml",
                "folder1/file2.yml",
                "folder2/file1.yml",
            ]
        )

    def test_files_and_folders(self) -> None:
        """Process mixed files and folders."""
        results = utils.iterate_inputs(iter(["file1.yml", "folder2"]), "YAML")
        names = sorted([str(path) for path in results])
        assert names == sorted(["file1.yml", "folder2/file1.yml"])

    def test_not_a_file_or_folder_relaxed(self) -> None:
        """Ignore inputs that are not files or folders."""
        results = utils.iterate_inputs(
            iter(["file1.yml", "unknown", "folder2"]), "YAML", strict=False
        )
        names = sorted([str(path) for path in results])
        assert names == sorted(["file1.yml", "folder2/file1.yml"])

    def test_not_a_file_or_folder_strict(self) -> None:
        """Raise an exception on inputs that are not files or folders."""
        with pytest.raises(IOError):
            list(
                utils.iterate_inputs(
                    iter(["file1.yml", "unknown", "folder2"]), "YAML", strict=True
                )
            )

    def test_xml_input(self) -> None:
        """Filter only the XML files, for XML2YAML (extract_questions)."""
        results = utils.iterate_inputs(
            iter(["file1.xml", "unknown", "folder1"]), "XML", strict=False
        )
        names = sorted([str(path) for path in results])
        assert names == sorted(["file1.xml", "folder1/file1.xml"])

    def test_not_supported_file_type(self) -> None:
        """Raise an exception on inputs that are not supported."""
        with pytest.raises(utils.ParsingError):
            list(utils.iterate_inputs(iter(["folder2"]), "XLSX"))


class TestUtils:
    def test_parse_markdown(self) -> None:
        eval_text = dedent(
            """
        # Really important question!

        Multiple choice question with Markdown

        ## Ordered list

        1. One
        2. Two
        3. Three

        ## Unordered list

        - One
        - Two
        - Three

        | Col1 | Col2 |
        |------|------|
        | 1    | 2    |

        <section markdown="1">

        | Col3 | Col4 |
        |------|------|
        | 3    | 4    |

        </section>
        """
        )

        expected_text = dedent(
            """
        <h1>Really important question!</h1>
        <p>Multiple choice question with Markdown</p>
        <h2>Ordered list</h2>
        <ol>
        <li>One</li>
        <li>Two</li>
        <li>Three</li>
        </ol>
        <h2>Unordered list</h2>
        <ul>
        <li>One</li>
        <li>Two</li>
        <li>Three</li>
        </ul>
        <table>
        <thead>
        <tr>
        <th>Col1</th>
        <th>Col2</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>1</td>
        <td>2</td>
        </tr>
        </tbody>
        </table>
        <section>
        <table>
        <thead>
        <tr>
        <th>Col3</th>
        <th>Col4</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>3</td>
        <td>4</td>
        </tr>
        </tbody>
        </table>
        </section>
        """
        )

        assert utils.parse_markdown(eval_text).strip() == expected_text.strip()

    def test_parse_markdown_html_issue(self) -> None:
        eval_text = dedent(
            """
        # Really important question!

        Multiple choice question with Markdown

        ## Ordered list

        1. One
        2. Two
        3. Three

        ## Unordered list

        - One
        - Two
        - Three

        | Col1 | Col2 |
        |------|------|
        | 1    | 2    |

        <section>

        | Col3 | Col4 |
        |------|------|
        | 3    | 4    |

        </section>
        """
        )

        expected_text = dedent(
            """
        <h1>Really important question!</h1>
        <p>Multiple choice question with Markdown</p>
        <h2>Ordered list</h2>
        <ol>
        <li>One</li>
        <li>Two</li>
        <li>Three</li>
        </ol>
        <h2>Unordered list</h2>
        <ul>
        <li>One</li>
        <li>Two</li>
        <li>Three</li>
        </ul>
        <table>
        <thead>
        <tr>
        <th>Col1</th>
        <th>Col2</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>1</td>
        <td>2</td>
        </tr>
        </tbody>
        </table>
        <section>

        | Col3 | Col4 |
        |------|------|
        | 3    | 4    |

        </section>
        """
        )

        assert utils.parse_markdown(eval_text).strip() == expected_text.strip()

    def test_table_styling(self) -> None:
        eval_text = dedent(
            """
        <table>
        <thead>
        <tr>
        <th>Col1</th>
        <th>Col2</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>1</td>
        <td>2</td>
        </tr>
        </tbody>
        </table>
        """
        )

        expected_text = dedent(
            """
        <table class="table table-sm w-auto">
        <thead>
        <tr>
        <th>Col1</th>
        <th>Col2</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>1</td>
        <td>2</td>
        </tr>
        </tbody>
        </table>
        """
        )

        assert utils.format_tables(eval_text).strip() == expected_text.strip()

    def test_inline_image(self) -> None:
        # TODO: Implement it
        assert True

    def test_preprocess_text(self) -> None:
        # TODO: Implement it
        assert True

    def test_load_questions(self) -> None:
        # TODO: Implement it extensively
        assert True

    def test_generate_moodle_questions(self) -> None:
        # TODO: Implement it extensively
        assert True

    def test_normalize_questions(self) -> None:
        # TODO: Implement it extensively. Not clear what it does.
        assert True

    def test_parse_code(self) -> None:
        input_code = dedent(
            """
        SELECT Name, Preis FROM Produkt
        WHERE Preis = (
            SELECT MAX(Preis)
            from Produkt
        ) ORDER BY Name ASC;
        """
        )

        expected_none_output = dedent(
            """
        SELECT Name, Preis FROM Produkt
        WHERE Preis = (
            SELECT MAX(Preis)
            from Produkt
        ) ORDER BY Name ASC;
        """
        ).strip()

        output = utils.parse_code(input_code).strip()

        assert output == expected_none_output

        expected_no_indent_output = dedent(
            """
        SELECT Name, Preis FROM Produkt
        WHERE Preis = (
            SELECT MAX(Preis)
            FROM Produkt
        ) ORDER BY Name ASC;
        """
        ).strip()

        output = utils.parse_code(input_code, parser="sqlparse-no-indent").strip()

        assert output == expected_no_indent_output

        expected_indent_output = dedent(
            """
        SELECT Name,
               Preis
        FROM Produkt
        WHERE Preis =
            (SELECT MAX(Preis)
             FROM Produkt)
        ORDER BY Name ASC;
        """
        ).strip()

        output = utils.parse_code(input_code, parser="sqlparse").strip()

        assert output == expected_indent_output

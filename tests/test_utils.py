from textwrap import dedent

from moodle_tools import utils


class TestUtils:
    def test_convert_markdown(self) -> None:
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
        """
        )

        assert utils.parse_markdown(eval_text).strip() == expected_text.strip()

    def test_table_borders(self) -> None:
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
        <table border="1px solid black" style="margin-bottom: 2ex">
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

        assert utils.add_table_borders(eval_text).strip() == expected_text.strip()

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

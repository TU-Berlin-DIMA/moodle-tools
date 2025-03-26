from textwrap import dedent

from moodle_tools import utils


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

        output = utils.format_code(input_code).strip()

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

        output = utils.format_code(input_code, formatter="sqlparse-no-indent").strip()

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

        output = utils.format_code(input_code, formatter="sqlparse").strip()

        assert output == expected_indent_output

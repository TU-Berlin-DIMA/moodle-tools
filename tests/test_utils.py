import pytest

from moodle_tools import utils

class TestUtils:
    def test_optional_text(self):
        
        evalText = 'Text'
        expectedText = '<![CDATA[Text]]>'
    
        assert utils.optional_text(evalText) == expectedText
        assert utils.optional_text(None) == ''
    
    def test_convert_markdown(self):
        assert True
    
    def test_table_borders(self):
        assert True

    def test_inline_image(self):
        assert True

    def test_preprocess_text(self):
        assert True

    def test_load_questions(self):
        assert True
    
    def test_generate_moodle_questions(self):
        assert True

    def test_normalize_questions(self):
        assert True
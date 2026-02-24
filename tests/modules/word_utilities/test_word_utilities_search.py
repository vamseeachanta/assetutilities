import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from test_utils import get_test_file_path

import pytest

from assetutilities.engine import engine


@pytest.mark.skip(reason="Only works in local drive")
def test_word_utilties_search_string():
    input_file = "word_utilities_search.yml"
    if input_file is not None and not os.path.isfile(input_file):
        input_file = get_test_file_path(input_file, os.path.dirname(__file__))
    result = engine(input_file)
    assert result is not None



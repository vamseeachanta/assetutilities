import os
from assetutilities.engine import engine


def run_read_pdf(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_read_pdf():
    input_file = "test_data/read_pdf.yml"
    result = run_read_pdf(input_file)
    assert result is not None


# test_read_pdf()

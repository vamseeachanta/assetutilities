import os
from src.assetutilities.engine import engine


def run_read_pdf(input_file):
    if input_file is not None and not os.path.isfile(input_file):
        input_file = os.path.join(os.path.dirname(__file__), input_file)
    result = engine(input_file)
    return result


def test_read_pdf():
    input_file = "test_data/read_pdf_pypdf2.yml"
    result = run_read_pdf(input_file)
    assert result is not None
        sys.argv.pop()

    run_read_pdf(input_file, expected_result)


# test_read_pdf()

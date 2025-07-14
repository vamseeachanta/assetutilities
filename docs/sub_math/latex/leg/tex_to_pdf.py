import os

# Third party imports
from pdflatex import PDFLaTeX

filename = "docs/sub_math/latex/document1.tex"
if os.path.isfile(filename):
    pdfl = PDFLaTeX.from_texfile(filename)
    pdf, log, completed_process = pdfl.create_pdf(
        keep_pdf_file=True, keep_log_file=True
    )
else:
    print(f"The file {filename} does not exist.")

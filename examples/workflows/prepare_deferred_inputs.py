"""Generate synthetic example inputs; no binary fixtures are retained in Git."""

from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure


def prepare(root):
    """Author text and CSV records whose expected contents are known directly.

    The two page strings and two CSV rows define the example answers. Figure
    positions are synthetic layout choices, not engineering acceptance limits.
    Existing inputs are preserved so running preparation twice is harmless.
    """
    root = Path(root)
    pdf_path = root / "read_pdf/outputs/input.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if not pdf_path.exists():
        with PdfPages(pdf_path) as pdf:
            for text in ("alpha page", "beta page"):
                figure = Figure()
                figure.text(0.1, 0.5, text)
                pdf.savefig(figure)
    csv_path = root / "csv_utilities/outputs/input.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        csv_path.write_bytes("name,value\ncafé,7\ntea,9\n".encode("latin1"))


if __name__ == "__main__":
    prepare(Path(__file__).parent)

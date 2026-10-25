"""Optionally regenerate the committed synthetic text inputs for the examples."""

from pathlib import Path


def _pdf_bytes():
    """Build an ASCII-only PDF with two authored pages and exact byte offsets."""
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [4 0 R 6 0 R] /Count 2 >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for text in ("alpha page", "beta page"):
        content_id = len(objects) + 2
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET\n"
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}endstream")
    document = "%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(document))
        document += f"{index} 0 obj\n{obj}\nendobj\n"
    xref = len(document)
    document += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    document += "".join(f"{offset:010} 00000 n \n" for offset in offsets)
    document += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    )
    return document.encode("ascii")


def prepare(root):
    """Restore missing inputs while preserving existing files byte for byte.

    Page text and CSV rows define the answers directly. Font, coordinates and
    page sizes are synthetic layout choices, not engineering acceptance limits.
    """
    root = Path(root)
    for name in ("read_pdf", "edit_pdf"):
        pdf_path = root / name / "input_data/input.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        if not pdf_path.exists():
            pdf_path.write_bytes(_pdf_bytes())
    csv_path = root / "csv_utilities/input_data/input.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        csv_path.write_bytes("name,value\ncafé,7\ntea,9\n".encode("utf-8"))


if __name__ == "__main__":
    prepare(Path(__file__).parent)

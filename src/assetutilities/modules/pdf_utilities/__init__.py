# ABOUTME: Package initialization for PDF utilities module
# ABOUTME: Provides PDF reading, editing, and comment extraction

# Lazy imports to avoid dependency issues
def __getattr__(name):
    if name == "ReadPDF":
        from assetutilities.modules.pdf_utilities.read_pdf import ReadPDF
        return ReadPDF
    elif name == "EditPDF":
        from assetutilities.modules.pdf_utilities.edit_pdf import EditPDF
        return EditPDF
    elif name == "PDFComments":
        from assetutilities.modules.pdf_utilities.pdf_comments import PDFComments
        return PDFComments
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ReadPDF",
    "EditPDF",
    "PDFComments",
]

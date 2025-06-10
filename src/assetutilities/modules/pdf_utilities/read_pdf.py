# import camelot
import tabula
import PyPDF2


class ReadPDF:

    def __init__(self) -> None:
        pass

    def read_pdf(self, cfg, file_index=0):
        parse_library = cfg.get("library", "tabula")
        if cfg["files"]["from_pdf"][file_index]["package"] == "camelot":
            df = self.from_pdf_camelot(cfg, file_index)
        elif parse_library == "PyPDF2":
            df = self.from_pdf_tabula(cfg, file_index)
        elif parse_library == "tabula":
            df = self.from_pdf_tabula(cfg, file_index)
        else:
            raise KeyError("PDF parsing library not programmed")

        return df

    def from_pdf_tabula(self, cfg, file_index=0):
        df = tabula.read_pdf(
            cfg["files"]["from_pdf"][file_index]["io"],
            pages=cfg["files"]["from_pdf"][file_index]["page"],
            multiple_tables=True,
        )
        return df

    def from_pdf_camelot(self, cfg, file_index=0):
        df = camelot.read_pdf(
            cfg["files"]["from_pdf"][file_index]["io"],
            pages=cfg["files"]["from_pdf"][file_index]["page"],
            suppress_stdout=False,
        )
        print(df)
        return df

    def from_pdf_PyPDF2(self, cfg, file_index=0):
        reader = PyPDF2.PdfReader(cfg["files"]["from_pdf"][file_index]["io"])
        page = reader.pages[3]

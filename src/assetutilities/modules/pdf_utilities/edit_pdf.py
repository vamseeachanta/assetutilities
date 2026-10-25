import logging
from pathlib import Path

import PyPDF2

logger = logging.getLogger(__name__)


class EditPDF:
    def __init__(self) -> None:
        pass

    def edit_pdf(self, cfg, file_index=None):
        parse_library = cfg.get("library", "PyPDF2")
        if parse_library == "PyPDF2":
            self.process_cfg_files(cfg, file_index)
        else:
            raise KeyError("PDF library not programmed")

    def process_cfg_files(self, cfg, file_index=None):
        if file_index is None:
            for file_index in range(0, len(cfg["files"])):
                self.from_pdf_PyPDF2(cfg, file_index)
        else:
            self.from_pdf_PyPDF2(cfg, file_index)

    def from_pdf_PyPDF2(self, cfg, file_index=None):
        file_name = cfg["files"][file_index]["io"]
        pages_groups = cfg["files"][file_index]["pages"]

        source = Path(file_name)
        pdf_reader = PyPDF2.PdfReader(source)
        folder = Path(
            cfg.get("Analysis", {}).get("result_folder", source.parent / "results")
        )
        folder.mkdir(parents=True, exist_ok=True)

        for pages in pages_groups:
            pdf_writer = PyPDF2.PdfWriter()
            page_range = range(pages[0], pages[1] + 1)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                if page_num in page_range:
                    pdf_writer.add_page(page)

            output = folder / f"{source.name}_page_{pages[0]}-{pages[1]}.pdf"
            with output.open("wb") as out:
                pdf_writer.write(out)

            logger.info("Created: %s", output.as_posix())

        # TODO Add results to cfg for tests

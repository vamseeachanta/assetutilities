"""
Report generation functionality for Markdown and Word outputs.
"""

import logging
from enum import Enum
from typing import Any, Dict

from .citations import (
    build_disclosure_section,
    build_provenance_section,
    build_references_section,
)
from .dom import DocumentDOM
from .writers import (
    DefaultDOCXWriter,
    DefaultMDWriter,
    DefaultHTMLWriter,
    ReportWriter,
    ReportWriterRegistry,
)


class ReportFormat(Enum):
    MARKDOWN = "md"
    WORD = "docx"
    HTML = "html"
    PDF = "pdf"


class ReportGenerator:
    def __init__(self):
        """Initialize generator with DOM"""
        self.dom = DocumentDOM()
        self.target_format = ReportFormat.MARKDOWN
        self.writer = None

    def initialize_from_config(self, config: Dict[str, Any]) -> None:
        """Initialize generator with config data"""
        self.writer = None
        self.dom.initialize_dom_from_config(config)
        if self.dom.references:
            self.dom.sections.extend(
                [
                    build_references_section(self.dom.references),
                    build_disclosure_section(),
                ]
            )
        flag = config.get("provenance", bool(self.dom.references))
        if not isinstance(flag, bool):
            raise ValueError("provenance must be a boolean")
        timestamped = self.dom.report_details.get("timestamped_filename", True)
        if not isinstance(timestamped, bool):
            raise ValueError("timestamped_filename must be a boolean")
        if flag:
            self.dom.sections.append(build_provenance_section(config))

        # Handle target report format
        format_type = self.dom.report_details.get("target_report_type", "md").lower()
        try:
            self.target_format = ReportFormat(format_type)
            logging.info(f"Set target format to: {self.target_format.value}")
        except ValueError:
            logging.warning(f"Unsupported format {format_type}, defaulting to markdown")
            self.target_format = ReportFormat.MARKDOWN

        # Check if writer class specified
        writer_class = self.dom.report_details.get("report_writer_class")
        if writer_class:
            paragraphs = [
                paragraph
                for section in [self.dom.first_section, *self.dom.sections]
                for paragraph in (
                    section.paragraphs
                    + [p for sub in section.subsections for p in sub["paragraphs"]]
                )
            ]
            if any(p.get("type") == "citation" for p in paragraphs) and (
                ReportWriterRegistry.get_writer(writer_class)
                not in (DefaultMDWriter, DefaultDOCXWriter, DefaultHTMLWriter)
            ):
                raise ValueError("citation paragraphs require a default writer")
            self._initialize_writer(writer_class)

    def _initialize_writer(self, writer_class: str) -> None:
        """Initialize the specified writer implementation"""
        if not ReportWriter.validate_writer_class(writer_class):
            logging.error(
                f"Invalid writer class {writer_class}, falling back to direct writing"
            )
            return

        try:
            writer_impl = ReportWriterRegistry.get_writer(writer_class)
            if writer_impl:
                self.writer = writer_impl(self.dom)
                logging.info(f"Initialized {writer_class}")
        except Exception as e:
            logging.error(f"Failed to initialize writer: {e}")
            self.writer = None

    def flush_report(self) -> None:
        """Generate report in target format"""
        # use user specified writer if specified and initialized
        if self.writer:
            logging.info("Using configured report writer")
            self.writer.flush()
            return

        # else Fallback to default writers
        if self.target_format == ReportFormat.MARKDOWN:
            writer = DefaultMDWriter(self.dom)
            writer.flush()
        elif self.target_format == ReportFormat.WORD:
            writer = DefaultDOCXWriter(self.dom)
            writer.flush()
        elif self.target_format == ReportFormat.HTML:
            DefaultHTMLWriter(self.dom).flush()
        elif self.target_format == ReportFormat.PDF:
            self._flush_pdf()

    # Remove _parse_markdown_table and _flush_docx methods as they're now in DefaultDOCXWriter
    def _flush_pdf(self) -> None:
        """Reject unsupported PDF output through the legacy writers."""
        raise NotImplementedError("PDF output needs reporting_standard: P6")


def run(config: Dict[str, Any]) -> None:
    """Entry point called by engine.py"""
    if config.get("reporting_standard") == "P6":
        from .standard import run as run_standard

        return run_standard(config)

    logging.info("Starting report generation...")
    generator = ReportGenerator()
    generator.initialize_from_config(config)
    generator.flush_report()

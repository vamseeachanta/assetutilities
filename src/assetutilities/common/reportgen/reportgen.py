"""
Report generation functionality for Markdown and Word outputs.
"""

import logging
from enum import Enum
from typing import Any, Dict

from .dom import DocumentDOM
from .writers import (
    DefaultDOCXWriter,
    DefaultMDWriter,
    ReportWriter,
    ReportWriterRegistry,
)


class ReportFormat(Enum):
    MARKDOWN = "md"
    WORD = "docx"
    PDF = "pdf"


class ReportGenerator:
    def __init__(self):
        """Initialize generator with DOM"""
        self.dom = DocumentDOM()
        self.target_format = ReportFormat.MARKDOWN
        self.writer = None

    def initialize_from_config(self, config: Dict[str, Any]) -> None:
        """Initialize generator with config data"""
        self.dom.initialize_dom_from_config(config)

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
        elif self.target_format == ReportFormat.PDF:
            self._flush_pdf()

    # Remove _parse_markdown_table and _flush_docx methods as they're now in DefaultDOCXWriter
    def _flush_pdf(self) -> None:
        """Generate PDF report"""
        # To be implemented
        logging.info("PDF format not yet implemented")
        pass


def run(config: Dict[str, Any]) -> None:
    """Entry point called by engine.py"""
    logging.info("Starting report generation...")
    generator = ReportGenerator()
    generator.initialize_from_config(config)
    generator.flush_report()

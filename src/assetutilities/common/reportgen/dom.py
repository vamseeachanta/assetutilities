"""
Document Object Model (DOM) for report generation.
"""

import threading
from typing import Any, ClassVar, Dict, List, Optional, Union

import sympy as im_sympy


class Section:
    def __init__(self, name: str, title: str = None):
        self.name = name
        self.title = title or name
        self.paragraphs: List[Dict[str, str]] = []  # Changed to match YAML structure
        self.subsections: List[Dict[str, Any]] = []  # Added for L2 sections


class DocumentDOM:
    LATEX_DELIM: str = "$"

    _instance: ClassVar[Optional["DocumentDOM"]] = None
    _lock = threading.Lock()  # Add class-level lock

    # - [ ] #todo #11_siva #acma_consultation add thread safety to singleton pattern
    def __new__(cls) -> "DocumentDOM":
        """Ensure single DOM instance with thread safety"""
        if cls._instance is None:
            with (
                cls._lock
            ):  # Acquire lock before checking again (double-checked locking)
                if cls._instance is None:  # Check again after acquiring lock
                    cls._instance = super().__new__(cls)
                    cls._instance.important_paths = {
                        "project_root": "",
                        "inputs_path": "",
                        "outputs_path": "",
                        "assets_path": "",
                    }
                    cls._instance.report_details = {
                        "name": "",
                        "client_logo": "",
                        "project_name": "",
                        "project_num": "",
                        "engineer": "",
                        "reviewer": "",
                        "date": "",
                        "target_file_stub": "",  # Added this
                        "target_report_type": "md",  # Default to markdown
                    }
                    cls._instance.first_section = Section("default")
                    cls._instance.sections: List[Section] = []
                    cls._instance.current_section: Optional[Section] = None
        return cls._instance

    def __init__(self):
        """Initialize DOM structure"""
        """
        pass
        # emptying this to fit singleton pattern
        self.important_paths = {
            "project_root": "",
            "inputs_path": "",
            "outputs_path": "",
            "assets_path": ""
        }
        self.report_details = {
            "name": "",
            "client_logo": "",
            "project_name": "",
            "project_num": "",
            "engineer": "",
            "reviewer": "",
            "date": "",
            "target_md_file": "",
            "target_word_file": ""
        }

        # Initialize first section as mandatory
        self.first_section = Section("default")
        self.sections: List[Section] = []
        self.current_section: Optional[Section] = None
        """

    def _initialize_first_section(self) -> None:
        """Initialize the first section with report details"""
        self.first_section.name = self.report_details["name"]
        table_content = (
            "| | |\n"
            "|:--|--:|\n"
            f"| Project Name | {self.report_details['project_name']} |\n"
            f"| Project # | {self.report_details['project_num']} |\n"
            f"| Engineer | {self.report_details['engineer']} |\n"
            f"| Checker | {self.report_details['reviewer']} |\n"
            f"| Date | {self.report_details['date']} |"
        )
        self.first_section.paragraphs = [
            {"type": "markdown_table", "content": table_content}
        ]

    def initialize_dom_from_config(self, config: Dict[str, Any]) -> None:
        """Initialize DOM from configuration dictionary"""
        self.report_details = config.get("report_details", {})
        self.important_paths = config.get("important_paths", {})

        # Set default target_report_type if not in config
        if "target_report_type" in config:
            self.report_details["target_report_type"] = config[
                "target_report_type"
            ].lower()
        elif "target_report_type" not in self.report_details:
            self.report_details["target_report_type"] = "md"

        # Initialize first section
        self._initialize_first_section()

        # Process all document sections
        if "sections_L1" in config:
            self._process_sections(config["sections_L1"])

    def _process_sections(self, sections_data: List[Dict[str, Any]]) -> None:
        """Process all sections from config data"""
        for section_data in sections_data:
            section = self.add_section(section_data["name"])
            self._process_paragraphs(section, section_data.get("paragraphs", []))
            self._process_subsections(section, section_data.get("sections_L2", []))

    def _process_subsections(
        self, section: Section, subsections_data: List[Dict[str, Any]]
    ) -> None:
        """Process subsections for a section"""
        if subsections_data:
            section.subsections = []
            for subsection in subsections_data:
                sub = {
                    "name": subsection["name"],
                    "paragraphs": [],  # Initialize empty paragraphs list
                }
                paragraphs = []
                # Process paragraphs first
                for para_list in subsection.get("paragraphs", []):
                    for para in para_list:
                        if isinstance(para, dict):
                            paragraphs.append(para)
                        else:
                            paragraphs.append({"type": "text", "content": para})
                sub["paragraphs"] = paragraphs
                section.subsections.append(sub)

    def _process_paragraphs(
        self, section: Union[Section, Dict[str, Any]], paragraphs_data: List[List[Any]]
    ) -> None:
        """Process paragraphs for a section or subsection dict"""
        if isinstance(section, dict):
            if "paragraphs" not in section:
                section["paragraphs"] = []
            target = section["paragraphs"]
        else:
            target = section.paragraphs

        for para_list in paragraphs_data:
            for para in para_list:
                if isinstance(para, dict):
                    target.append(para)
                else:
                    target.append({"type": "text", "content": para})

    def add_section(self, name: str, title: str = None) -> Section:
        """Add a new section to the document"""
        section = Section(name, title)
        self.sections.append(section)
        self.current_section = section
        return section

    def switch_to_section(self, name: str) -> Section:
        """Switch to an existing section or create new if not exists"""
        for section in self.sections:
            if section.name == name:
                self.current_section = section
                return section
        return self.add_section(name)

    def add_paragraph(self, text: str) -> None:
        """Add a plain text paragraph to current section"""
        if not self.current_section:
            self.add_section("default")
        self.current_section.paragraphs.append({"type": "text", "content": text})

    """
        Adds a sympy expression as a paragraph to the current section
    """

    def add_sympy_expression(self, text: str, expr: im_sympy.Expr) -> None:
        """Append text and im_sympy expression to current section"""
        if not self.current_section:
            self.add_section("default")
        self.current_section.paragraphs.append({"type": "text", "content": text})
        self.current_section.paragraphs.append(
            {"type": "im_sympy", "content": im_sympy.latex(expr)}
        )


"""

untracked (in git) issues and backlog


"""

"""PDF Processing Module for Web Contextualization."""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Process PDF files and extract text, tables, and metadata."""
    
    def __init__(self, output_dir: Path):
        """Initialize PDF processor with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to import PDF processing libraries
        self.pypdf2_available = False
        self.pdfplumber_available = False
        self.pymupdf_available = False
        
        try:
            import PyPDF2
            self.pypdf2_available = True
            logger.info("PyPDF2 available for PDF processing")
        except ImportError:
            pass
        
        try:
            import pdfplumber
            self.pdfplumber_available = True
            logger.info("pdfplumber available for advanced PDF processing")
        except ImportError:
            pass
        
        try:
            import fitz  # PyMuPDF
            self.pymupdf_available = True
            logger.info("PyMuPDF available for PDF processing")
        except ImportError:
            pass
    
    def process_pdf(self, pdf_path: Path, extract_images: bool = False,
                   extract_tables: bool = True) -> Tuple[Optional[Path], Dict[str, Any]]:
        """Process a PDF file and extract content."""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None, {"error": "File not found"}
        
        # Generate output path
        output_name = pdf_path.stem + "_extracted.txt"
        output_path = self.output_dir / output_name
        
        metadata = {
            "source_file": str(pdf_path),
            "extraction_method": None,
            "page_count": 0,
            "tables_extracted": 0,
            "images_extracted": 0
        }
        
        # Try different extraction methods in order of preference
        text_content = ""
        
        if self.pdfplumber_available:
            text_content, meta = self._extract_with_pdfplumber(
                pdf_path, extract_tables, extract_images
            )
            metadata.update(meta)
            metadata["extraction_method"] = "pdfplumber"
        
        elif self.pymupdf_available:
            text_content, meta = self._extract_with_pymupdf(
                pdf_path, extract_images
            )
            metadata.update(meta)
            metadata["extraction_method"] = "pymupdf"
        
        elif self.pypdf2_available:
            text_content, meta = self._extract_with_pypdf2(pdf_path)
            metadata.update(meta)
            metadata["extraction_method"] = "pypdf2"
        
        else:
            # Fallback to system tools if available
            text_content, meta = self._extract_with_system_tools(pdf_path)
            metadata.update(meta)
            metadata["extraction_method"] = "system_tools"
        
        if text_content:
            # Save extracted text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Save metadata
            meta_path = output_path.with_suffix('.meta.json')
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Extracted {len(text_content)} characters from {pdf_path.name}")
            return output_path, metadata
        
        logger.error(f"Failed to extract text from {pdf_path}")
        return None, metadata
    
    def _extract_with_pdfplumber(self, pdf_path: Path, extract_tables: bool,
                                extract_images: bool) -> Tuple[str, Dict]:
        """Extract using pdfplumber (best for tables and complex layouts)."""
        try:
            import pdfplumber
            
            text_parts = []
            metadata = {"page_count": 0, "tables_extracted": 0}
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata["page_count"] = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages, 1):
                    text_parts.append(f"\n--- Page {i} ---\n")
                    
                    # Extract main text
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    
                    # Extract tables
                    if extract_tables:
                        tables = page.extract_tables()
                        for j, table in enumerate(tables, 1):
                            if table:
                                text_parts.append(f"\n[Table {i}.{j}]\n")
                                # Convert table to text format
                                for row in table:
                                    row_text = " | ".join(
                                        str(cell) if cell else "" for cell in row
                                    )
                                    text_parts.append(row_text)
                                text_parts.append("")
                                metadata["tables_extracted"] += 1
            
            return "\n".join(text_parts), metadata
            
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return "", {"error": str(e)}
    
    def _extract_with_pymupdf(self, pdf_path: Path,
                              extract_images: bool) -> Tuple[str, Dict]:
        """Extract using PyMuPDF (good balance of speed and quality)."""
        try:
            import fitz  # PyMuPDF
            
            text_parts = []
            metadata = {"page_count": 0, "images_extracted": 0}
            
            pdf = fitz.open(pdf_path)
            metadata["page_count"] = len(pdf)
            
            for i, page in enumerate(pdf, 1):
                text_parts.append(f"\n--- Page {i} ---\n")
                
                # Extract text
                text = page.get_text()
                if text:
                    text_parts.append(text)
                
                # Extract images if requested
                if extract_images:
                    image_list = page.get_images(full=True)
                    if image_list:
                        text_parts.append(f"\n[Page {i} contains {len(image_list)} images]\n")
                        metadata["images_extracted"] += len(image_list)
            
            pdf.close()
            return "\n".join(text_parts), metadata
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return "", {"error": str(e)}
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> Tuple[str, Dict]:
        """Extract using PyPDF2 (basic text extraction)."""
        try:
            import PyPDF2
            
            text_parts = []
            metadata = {"page_count": 0}
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["page_count"] = len(pdf_reader.pages)
                
                for i, page in enumerate(pdf_reader.pages, 1):
                    text_parts.append(f"\n--- Page {i} ---\n")
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n".join(text_parts), metadata
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return "", {"error": str(e)}
    
    def _extract_with_system_tools(self, pdf_path: Path) -> Tuple[str, Dict]:
        """Fallback to system tools like pdftotext."""
        try:
            import subprocess
            
            # Try pdftotext (from poppler-utils)
            result = subprocess.run(
                ['pdftotext', '-layout', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout, {"extraction_method": "pdftotext"}
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.warning(f"System tool extraction failed: {e}")
        
        return "", {"error": "No PDF extraction tools available"}
    
    def extract_formulas(self, pdf_path: Path) -> List[str]:
        """Extract mathematical formulas from PDF (specialized)."""
        formulas = []
        
        # This would require specialized libraries like pdf2image + OCR
        # or mathematical formula extraction tools
        # For now, return empty list as placeholder
        
        logger.info("Formula extraction not yet implemented")
        return formulas
    
    def extract_diagrams_metadata(self, pdf_path: Path) -> List[Dict]:
        """Extract metadata about diagrams and figures."""
        diagrams = []
        
        # This would analyze page layout to identify figures
        # For now, return empty list as placeholder
        
        logger.info("Diagram metadata extraction not yet implemented")
        return diagrams
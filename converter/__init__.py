"""
converter package
------------------
Self-contained PDF -> DOCX conversion engine used by app.py.

Public API:
    convert_pdf_to_docx(pdf_path, output_path) -> str
"""

from .converter import convert_pdf_to_docx, ConversionError

__all__ = ["convert_pdf_to_docx", "ConversionError"]

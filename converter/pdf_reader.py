"""
pdf_reader.py
-------------
Responsible for opening and validating a PDF before conversion.

Fidelity note: DocForge treats the PDF as the single source of truth.
This module intentionally does NOT extract text into flat paragraphs
or otherwise pre-process content — any such step would mean re-flowing
the document, which risks losing exact position, spacing, and layout.
Instead, it verifies the file is a readable, unprotected PDF and
reports basic structural facts (page count, page sizes) that the rest
of the app can use for validation and logging. The actual page-by-page
layout reconstruction is delegated to doc_writer.py, which reproduces
text position, tables, images, and styling directly from the PDF.
"""

from dataclasses import dataclass

import fitz  # PyMuPDF


class PdfReadError(Exception):
    """Raised when a PDF cannot be opened or is unsuitable for conversion."""


@dataclass
class PdfInfo:
    """Basic structural facts about a validated PDF."""
    page_count: int
    page_sizes: list  # list[tuple[float, float]] width/height in points, per page


def inspect_pdf(pdf_path: str) -> PdfInfo:
    """
    Open a PDF just far enough to validate it and read its structure,
    without altering or flattening any content.

    Raises PdfReadError if the file cannot be opened, is encrypted, or
    contains no pages.
    """
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise PdfReadError(f"Could not open PDF: {exc}") from exc

    try:
        if document.is_encrypted:
            raise PdfReadError(
                "This PDF is password-protected and can't be converted yet."
            )

        if document.page_count == 0:
            raise PdfReadError("The PDF has no pages.")

        page_sizes = [
            (page.rect.width, page.rect.height) for page in document
        ]

        return PdfInfo(page_count=document.page_count, page_sizes=page_sizes)
    finally:
        document.close()

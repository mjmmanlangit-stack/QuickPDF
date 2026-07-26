"""
converter.py
------------
Orchestrates the end-to-end PDF -> DOCX workflow by coordinating
pdf_reader.py (validation) and doc_writer.py (layout-faithful
generation).

app.py should only ever need to call convert_pdf_to_docx() from here;
it should never talk to pdf_reader or doc_writer directly.
"""

from .pdf_reader import inspect_pdf, PdfReadError
from .doc_writer import write_docx, DocWriteError


class ConversionError(Exception):
    """Raised when a PDF cannot be converted to DOCX for any reason."""


def convert_pdf_to_docx(pdf_path: str, output_path: str) -> str:
    """
    Convert a PDF file at pdf_path into a DOCX file at output_path,
    preserving the original layout as closely as possible.

    Returns output_path on success. Raises ConversionError with a
    user-friendly message on any failure.
    """
    try:
        inspect_pdf(pdf_path)
    except PdfReadError as exc:
        raise ConversionError(str(exc)) from exc

    try:
        write_docx(pdf_path, output_path)
    except DocWriteError as exc:
        raise ConversionError("Unable to convert this PDF.") from exc

    return output_path

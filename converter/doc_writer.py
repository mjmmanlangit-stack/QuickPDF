"""
doc_writer.py
-------------
Responsible for generating the .docx file that reproduces a PDF's
layout as faithfully as possible.

Fidelity is the top priority for this module: page size, margins,
text position, reading order, fonts, colors, bold/italic, tables with
borders, and images at their original size and placement must all be
preserved. Reflowing content into fresh paragraphs, merging text,
re-aligning, or "cleaning up" the layout is explicitly avoided, even
when doing so would produce a simpler or more conventionally editable
document.

To meet that bar this module delegates the actual page-by-page
reconstruction to pdf2docx (github.com/dothinking/pdf2docx), a
PyMuPDF-based engine purpose-built for layout-preserving PDF -> DOCX
conversion — including tables, images, multi-column text, and per-run
styling — rather than hand-rolled text extraction. Everything still
runs fully offline; no network calls are made.
"""

from pdf2docx import Converter


class DocWriteError(Exception):
    """Raised when a DOCX file cannot be generated or saved."""


def write_docx(pdf_path: str, output_path: str) -> None:
    """
    Generate a .docx file at output_path that visually matches the
    PDF at pdf_path as closely as possible, preserving its original
    page size, layout, tables, images, and styling.

    Raises DocWriteError on failure.
    """
    converter = None
    try:
        converter = Converter(pdf_path)
        # start=0 -> convert every page, in original order.
        # multi_processing is left off so behaviour stays predictable
        # and fully offline on machines without spare cores.
        converter.convert(output_path, start=0, end=None)
    except Exception as exc:
        raise DocWriteError(f"Could not generate DOCX: {exc}") from exc
    finally:
        if converter is not None:
            converter.close()

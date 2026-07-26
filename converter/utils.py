"""
utils.py
--------
Small, focused helper functions shared across the converter package:
input validation, safe filename generation, and temporary file cleanup.

Keeping these helpers isolated means converter.py and app.py stay free
of low-level string/file bookkeeping.
"""

import os
import re
import time
import uuid


ALLOWED_EXTENSION = ".pdf"
PDF_MAGIC_BYTES = b"%PDF-"


def is_pdf_file(filename: str, file_bytes: bytes) -> bool:
    """
    Validate that an uploaded file is genuinely a PDF.

    Checks both the file extension and the PDF magic number so a
    renamed non-PDF file (e.g. "fake.pdf") is still rejected.
    """
    if not filename:
        return False

    has_pdf_extension = filename.lower().endswith(ALLOWED_EXTENSION)
    has_pdf_signature = file_bytes[:5] == PDF_MAGIC_BYTES

    return has_pdf_extension and has_pdf_signature


def sanitize_filename(filename: str) -> str:
    """
    Strip path separators and unsafe characters from a filename,
    keeping only the base name so it is safe to use on disk.
    """
    base_name = os.path.basename(filename)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", base_name)
    return safe_name or "document"


def generate_unique_filename(original_filename: str, extension: str) -> str:
    """
    Build a collision-free filename for a temporary or output file,
    derived from the original name plus a short unique token.
    """
    safe_original = sanitize_filename(original_filename)
    stem = os.path.splitext(safe_original)[0]
    unique_token = uuid.uuid4().hex[:8]
    return f"{stem}_{unique_token}{extension}"


def cleanup_file(path: str) -> None:
    """
    Remove a file from disk if it exists, silently ignoring errors.
    Used to clear uploads/temp artifacts after a conversion completes.
    """
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def cleanup_stale_files(directory: str, max_age_seconds: int = 3600) -> None:
    """
    Remove files older than max_age_seconds from a working directory
    (uploads/, output/, temp/) to prevent unbounded disk growth.
    """
    if not os.path.isdir(directory):
        return

    now = time.time()
    for entry in os.scandir(directory):
        try:
            if entry.is_file() and (now - entry.stat().st_mtime) > max_age_seconds:
                os.remove(entry.path)
        except OSError:
            pass

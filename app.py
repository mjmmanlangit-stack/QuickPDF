"""
app.py
------
DocForge's Flask entry point.

Kept intentionally small: this file only receives uploads, validates
them, calls the converter package, and returns the result. All
conversion logic lives in converter/.
"""

import os
import sys
import tempfile

from flask import Flask, render_template, request, jsonify, send_from_directory

from converter import convert_pdf_to_docx, ConversionError
from converter.utils import (
    is_pdf_file,
    generate_unique_filename,
    cleanup_file,
    cleanup_stale_files,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# When frozen into a standalone executable (PyInstaller), templates and
# static assets are unpacked into a bundle directory at sys._MEIPASS,
# and the bundle itself may not be writable — so working directories
# for uploads/output/temp fall back to the OS temp folder instead.
IS_FROZEN = getattr(sys, "frozen", False)
RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
WORK_DIR = os.path.join(tempfile.gettempdir(), "DocForge") if IS_FROZEN else BASE_DIR

UPLOAD_DIR = os.path.join(WORK_DIR, "uploads")
OUTPUT_DIR = os.path.join(WORK_DIR, "output")
TEMP_DIR = os.path.join(WORK_DIR, "temp")

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

app = Flask(
    __name__,
    template_folder=os.path.join(RESOURCE_DIR, "templates"),
    static_folder=os.path.join(RESOURCE_DIR, "static"),
)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE_BYTES

for directory in (UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR):
    os.makedirs(directory, exist_ok=True)


@app.route("/")
def index():
    """Render the single-page DocForge interface."""
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    """
    Accept a PDF upload, convert it to DOCX, and return the download
    filename as JSON. The browser then requests /download/<filename>.
    """
    cleanup_stale_files(UPLOAD_DIR)
    cleanup_stale_files(OUTPUT_DIR)

    uploaded_file = request.files.get("file")
    if uploaded_file is None or uploaded_file.filename == "":
        return jsonify(success=False, error="Please choose a PDF file."), 400

    file_bytes = uploaded_file.read()
    if not is_pdf_file(uploaded_file.filename, file_bytes):
        return jsonify(success=False, error="Please upload a valid PDF."), 400

    upload_filename = generate_unique_filename(uploaded_file.filename, ".pdf")
    upload_path = os.path.join(UPLOAD_DIR, upload_filename)

    output_filename = generate_unique_filename(uploaded_file.filename, ".docx")
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        with open(upload_path, "wb") as saved_file:
            saved_file.write(file_bytes)

        convert_pdf_to_docx(upload_path, output_path)
    except ConversionError as exc:
        cleanup_file(output_path)
        return jsonify(success=False, error=str(exc)), 422
    except Exception:
        cleanup_file(output_path)
        return jsonify(success=False, error="Unable to convert this PDF."), 500
    finally:
        cleanup_file(upload_path)

    return jsonify(success=True, filename=output_filename)


@app.route("/download/<path:filename>")
def download(filename):
    """Serve a converted DOCX file for download."""
    return send_from_directory(
        OUTPUT_DIR,
        filename,
        as_attachment=True,
        download_name="converted.docx",
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

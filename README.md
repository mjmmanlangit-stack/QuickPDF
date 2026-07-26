# DocForge

A premium, fully offline PDF → DOCX converter. Drop in a PDF, click **Convert**, and download an editable Word document — nothing ever leaves your computer.

![DocForge](static/images/screenshot-placeholder.png)

---

## Overview

DocForge is a lightweight local web application built with Flask and vanilla JavaScript. It focuses on doing one thing extremely well: converting PDF documents into editable `.docx` files, with a clean, modern interface and no unnecessary features.

There is no login, no database, no cloud storage, and no telemetry. The app runs entirely on `localhost`, and every file you convert is processed and stored only on your own machine.

## Features

- **Drag & drop or browse** — upload a PDF in one click or by dragging it onto the window
- **Layout-faithful conversion** — reproduces the original page size, margins, text position, fonts, colors, bold/italic, tables with borders, and images at their original placement, rather than re-flowing content into fresh paragraphs
- **Fully offline** — no internet connection, external APIs, or CDNs required at runtime
- **Private by design** — no accounts, no analytics, no data collection
- **Premium interface** — glassmorphism card, animated ambient background, and smooth micro-interactions
- **Automatic cleanup** — uploaded and generated files are removed automatically after a short period

### Conversion philosophy

DocForge treats the PDF as the single source of truth. The converter never merges paragraphs, rearranges text, reflows layout, or "cleans up" formatting — if a layout element can't be reproduced perfectly, the original visual appearance is preserved rather than simplified. Conversion is powered by [pdf2docx](https://github.com/dothinking/pdf2docx), an offline, PyMuPDF-based engine built specifically for layout reconstruction (as opposed to a generic text extractor), which is why DocForge can preserve tables, images, and exact positioning rather than just plain text.

Two things are outside what any offline, editable-output converter can guarantee today:
- **Password-protected PDFs** are currently rejected with a clear message rather than guessed at (see roadmap).
- Extremely complex layouts (dense multi-column magazine layouts, heavily overlapping elements) are reproduced as closely as the DOCX format allows, but pixel-perfect fidelity on every edge case isn't guaranteed while keeping the output genuinely editable.

## Installation

### 1. Clone or download the project

```bash
git clone <your-repo-url> DocForge
cd DocForge
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it:

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the application

```bash
python app.py
```

Then open your browser to:

```
http://127.0.0.1:5000
```

Upload a PDF, click **Convert to DOCX**, and download your file once the conversion completes.

## Project structure

```
DocForge/
│
├── app.py                 # Thin Flask entry point: routes, validation, responses
├── requirements.txt        # Python dependencies
├── README.md
│
├── templates/
│   └── index.html          # Single-page application UI
│
├── static/
│   ├── css/
│   │   └── style.css       # Premium monochrome theme & animations
│   ├── js/
│   │   └── script.js       # Drag & drop, upload, and state handling
│   └── images/
│
├── converter/               # Conversion engine (business logic)
│   ├── converter.py         # Orchestrates the PDF -> DOCX workflow
│   ├── pdf_reader.py        # Validates the PDF (pages, encryption) without altering it
│   ├── doc_writer.py        # Generates a layout-faithful .docx via pdf2docx
│   └── utils.py             # Validation, filenames, cleanup helpers
│
├── uploads/                 # Temporary storage for incoming PDFs
├── output/                  # Generated DOCX files ready for download
└── temp/                    # Scratch space for intermediate processing
```

## Desktop application

DocForge can also run as a native desktop app instead of a browser tab — same interface, no address bar, no browser chrome. It works by running the existing Flask app in a background thread and opening it inside a native OS window with [pywebview](https://pywebview.flowrl.com/).

### Run it as a desktop app (no packaging)

```bash
pip install -r requirements.txt -r requirements-desktop.txt
python desktop_app.py
```

A native window titled **DocForge** opens with the app already running inside it.

### Build a standalone executable

Once `requirements-desktop.txt` is installed, freeze the app with PyInstaller. Run the build **on the OS you're targeting** — PyInstaller does not cross-compile.

**macOS / Linux:**

```bash
pyinstaller --noconfirm --onefile --windowed --name DocForge \
  --add-data "templates:templates" \
  --add-data "static:static" \
  desktop_app.py
```

**Windows (PowerShell / cmd):**

```bash
pyinstaller --noconfirm --onefile --windowed --name DocForge ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  desktop_app.py
```

The finished executable is written to `dist/DocForge` (`dist/DocForge.exe` on Windows). It can be copied and run on another machine of the same OS without needing Python installed.

### Platform notes for pywebview

pywebview uses the OS's built-in web engine rather than bundling its own browser, so system requirements are minimal but vary slightly:

- **Windows** — uses the Edge WebView2 runtime, preinstalled on Windows 10/11.
- **macOS** — uses the built-in WebKit engine; no extra install needed.
- **Linux** — requires GTK + WebKit2GTK system packages, e.g. on Debian/Ubuntu: `sudo apt install python3-gi gir1.2-webkit2-4.0`.

All conversion logic, storage, and processing remain 100% local — going desktop only changes how the interface is displayed, not how the app works.

### Native downloads

In the desktop app, clicking **Download DOCX** doesn't behave like a browser download — it calls straight into Python (via pywebview's JS API) to copy the converted file directly into your real Windows **Downloads** folder, then shows a confirmation with **Open File**, **Open Downloads Folder**, and **Convert another file** actions. If a file with the same name already exists there, it's saved alongside it as `name (1).docx`, `name (2).docx`, etc. — nothing already in Downloads is ever overwritten. Running the app in a plain browser tab (`python app.py`) is unaffected and keeps the standard browser download behavior.

## Screenshots

_Add screenshots of the landing screen, drag & drop state, and success state here._

## Future roadmap

The following features are intentionally **not implemented** in this version, to keep DocForge focused and fast. They may be considered for future releases:

- OCR support for scanned PDFs
- Batch conversion of multiple files
- Image extraction alongside text
- PDF compression
- Merge multiple PDFs
- Split a PDF into separate files
- Support for password-protected PDFs
- Dark mode
- DOCX to PDF conversion

## License

This project is provided under the MIT License. See `LICENSE` for details.

Ang pinaka importante is kahit anong hirap ng buhay, wag na wag ka magshash*bu.

"""
desktop_app.py
---------------
Runs DocForge as a native desktop application instead of a browser tab.

It starts the existing Flask app (app.py) on a local port in a
background thread, then opens a native OS window pointed at it using
pywebview — no address bar, no browser tabs, just the app.

This module also exposes a small "JS API" (the Api class below) to the
frontend running inside the webview. The browser's own download
mechanism can't reliably write to a real Downloads folder or open
files/folders from inside a sandboxed webview, so those native
operations — saving the converted file to the user's actual Downloads
folder, and opening a file or folder with the OS's default handler —
are done here in Python instead, and called directly from script.js
via `window.pywebview.api`.

Run directly with:
    python desktop_app.py

Or freeze it into a standalone executable with PyInstaller — see the
"Desktop Application" section of README.md for platform-specific
build commands.
"""

import ctypes
import os
import re
import shutil
import subprocess
import sys
import threading

import webview

from app import app as flask_app, OUTPUT_DIR

HOST = "127.0.0.1"
PORT = 5000

# Characters that are illegal in Windows filenames, plus other OSes'
# path separators, so a filename is safe to save on any platform.
_ILLEGAL_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def start_flask_server() -> None:
    """Run the Flask app quietly in the background (no reloader/debug)."""
    flask_app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def get_downloads_folder() -> str:
    """
    Resolve the current user's real Downloads folder.

    On Windows this asks the OS directly (via the Known Folder API) so
    it's correct even if the user has relocated Downloads (e.g. onto
    OneDrive or another drive). Falls back to "~/Downloads" everywhere
    else, and if the Windows lookup fails for any reason.
    """
    if os.name == "nt":
        windows_path = _windows_known_downloads_folder()
        if windows_path:
            return windows_path

    return os.path.join(os.path.expanduser("~"), "Downloads")


def _windows_known_downloads_folder() -> str | None:
    """Look up the Downloads folder via SHGetKnownFolderPath (Windows only)."""
    try:
        FOLDERID_DOWNLOADS = "{374DE290-123F-4565-9164-39C4925E467B}"

        guid = ctypes.create_string_buffer(16)
        result = ctypes.windll.ole32.CLSIDFromString(
            ctypes.c_wchar_p(FOLDERID_DOWNLOADS), ctypes.byref(guid)
        )
        if result != 0:
            return None

        path_ptr = ctypes.c_wchar_p()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(guid), 0, 0, ctypes.byref(path_ptr)
        )
        if result != 0 or not path_ptr.value:
            return None

        path = path_ptr.value
        ctypes.windll.ole32.CoTaskMemFree(path_ptr)
        return path
    except Exception:
        return None


def sanitize_download_filename(filename: str) -> str:
    """
    Strip characters that are illegal in a filename on the current OS,
    keeping the name otherwise human-readable (spaces, punctuation).
    """
    name = os.path.basename(filename or "").strip()
    name = _ILLEGAL_FILENAME_CHARS.sub("", name)
    name = name.rstrip(" .")  # Windows disallows trailing dots/spaces
    return name or "document.docx"


def unique_destination_path(directory: str, filename: str) -> str:
    """
    Build a collision-free path inside directory, following the same
    "name (1).ext" convention Windows Explorer uses, so a repeat
    conversion doesn't silently overwrite a previous download.
    """
    stem, extension = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)

    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{stem} ({counter}){extension}")
        counter += 1

    return candidate


def open_with_default_app(path: str) -> None:
    """Open a file or folder using the OS's default handler."""
    if os.name == "nt":
        os.startfile(path)  # noqa: S606 - intentional, opens with default app
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class Api:
    """
    Methods on this class are automatically exposed to the frontend as
    `window.pywebview.api.<method_name>(...)` once the webview is
    ready. Each call returns a plain dict so script.js can branch on
    `result.success` without needing to catch exceptions across the
    JS <-> Python bridge.
    """

    def save_to_downloads(self, server_filename: str, desired_filename: str = None) -> dict:
        """
        Copy a converted file that already exists in OUTPUT_DIR into
        the user's real Downloads folder, under a human-friendly name.
        """
        try:
            source_path = os.path.join(OUTPUT_DIR, server_filename)
            if not os.path.isfile(source_path):
                return {"success": False, "error": "The converted file could not be found."}

            downloads_dir = get_downloads_folder()
            os.makedirs(downloads_dir, exist_ok=True)

            safe_name = sanitize_download_filename(desired_filename or server_filename)
            destination_path = unique_destination_path(downloads_dir, safe_name)

            shutil.copyfile(source_path, destination_path)

            return {
                "success": True,
                "path": destination_path,
                "filename": os.path.basename(destination_path),
                "folder": downloads_dir,
            }
        except PermissionError:
            return {
                "success": False,
                "error": "Permission denied while saving to Downloads. Try running as your normal user account.",
            }
        except OSError as exc:
            return {"success": False, "error": f"Couldn't save the file: {exc.strerror or exc}"}
        except Exception as exc:
            return {"success": False, "error": f"Couldn't save the file: {exc}"}

    def open_path(self, path: str) -> dict:
        """Open a file or folder with the OS's default application."""
        try:
            if not path or not os.path.exists(path):
                return {"success": False, "error": "That file or folder no longer exists."}
            open_with_default_app(path)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": f"Couldn't open that location: {exc}"}


def main() -> None:
    server_thread = threading.Thread(target=start_flask_server, daemon=True)
    server_thread.start()

    api = Api()

    webview.create_window(
        "QuickPDF",
        f"http://{HOST}:{PORT}",
        width=560,
        height=780,
        min_size=(420, 640),
        resizable=True,
        background_color="#F7F7F7",
        js_api=api,
    )
    webview.start()


if __name__ == "__main__":
    main()

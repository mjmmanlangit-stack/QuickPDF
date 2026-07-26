/**
 * script.js
 * ---------
 * Client-side behaviour for DocForge: file selection (drag & drop or
 * browse), triggering the /convert request, and switching between the
 * idle, loading, success, and error panel states.
 *
 * This same file runs in two contexts:
 *   1. A regular browser tab (`python app.py`) — the Download button
 *      is a plain <a download> link and the browser handles saving.
 *   2. The desktop app window (`python desktop_app.py` / the packaged
 *      .exe) — pywebview injects `window.pywebview.api`, and clicking
 *      Download instead calls into Python to save the file straight
 *      to the user's real Downloads folder and show a native-feeling
 *      confirmation modal with Open File / Open Folder actions.
 */

(function () {
  "use strict";

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const chooseFileBtn = document.getElementById("choose-file-btn");
  const selectedFile = document.getElementById("selected-file");
  const selectedFileName = document.getElementById("selected-file-name");
  const clearFileBtn = document.getElementById("clear-file-btn");
  const convertBtn = document.getElementById("convert-btn");

  const panelIdle = document.getElementById("panel-idle");
  const panelLoading = document.getElementById("panel-loading");
  const panelSuccess = document.getElementById("panel-success");
  const panelError = document.getElementById("panel-error");

  const downloadBtn = document.getElementById("download-btn");
  const successFilename = document.getElementById("success-filename");
  const errorMessage = document.getElementById("error-message");

  const convertAnotherBtn = document.getElementById("convert-another-btn");
  const tryAgainBtn = document.getElementById("try-again-btn");
  const toastStack = document.getElementById("toast-stack");

  const downloadSuccessModal = document.getElementById("download-success-modal");
  const downloadErrorModal = document.getElementById("download-error-modal");
  const modalLocation = document.getElementById("modal-location");
  const modalFilename = document.getElementById("modal-filename");
  const modalOpenFileBtn = document.getElementById("modal-open-file-btn");
  const modalOpenFolderBtn = document.getElementById("modal-open-folder-btn");
  const modalConvertAnotherBtn = document.getElementById("modal-convert-another-btn");
  const modalErrorMessage = document.getElementById("modal-error-message");
  const modalErrorCloseBtn = document.getElementById("modal-error-close-btn");

  let currentFile = null;
  let lastConvertedServerFilename = null; // filename inside the app's output/ dir
  let lastSavedFilePath = null;           // full path once saved to Downloads
  let lastSavedFolderPath = null;

  /* -------------------------------------------------------------------- */
  /* Desktop (pywebview) detection                                        */
  /* -------------------------------------------------------------------- */

  let isDesktopApp = false;

  // pywebview injects window.pywebview once the native window is ready;
  // on some platforms this can happen slightly after page load, so we
  // listen for the ready event as well as checking eagerly below.
  window.addEventListener("pywebviewready", () => {
    isDesktopApp = true;
  });

  function isDesktopEnvironment() {
    return isDesktopApp || (typeof window.pywebview !== "undefined" && !!window.pywebview.api);
  }

  /* -------------------------------------------------------------------- */
  /* Panel switching                                                       */
  /* -------------------------------------------------------------------- */

  function showPanel(panel) {
    [panelIdle, panelLoading, panelSuccess, panelError].forEach((p) => {
      p.hidden = p !== panel;
    });
  }

  /* -------------------------------------------------------------------- */
  /* File selection                                                        */
  /* -------------------------------------------------------------------- */

  function setFile(file) {
    if (!file) return;

    if (!isLikelyPdf(file)) {
      showToast("Please upload a valid PDF.", "error");
      return;
    }

    currentFile = file;
    selectedFileName.textContent = file.name;
    selectedFile.hidden = false;
    convertBtn.disabled = false;
  }

  function isLikelyPdf(file) {
    const nameLooksPdf = file.name.toLowerCase().endsWith(".pdf");
    const typeLooksPdf = file.type === "application/pdf" || file.type === "";
    return nameLooksPdf && typeLooksPdf;
  }

  function clearFile() {
    currentFile = null;
    fileInput.value = "";
    selectedFile.hidden = true;
    convertBtn.disabled = true;
  }

  chooseFileBtn.addEventListener("click", (event) => {
    // The label already opens the file picker; prevent double firing
    // when the button itself is clicked directly.
    event.preventDefault();
    fileInput.click();
  });

  fileInput.addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    setFile(file);
  });

  clearFileBtn.addEventListener("click", (event) => {
    event.preventDefault();
    clearFile();
  });

  /* -------------------------------------------------------------------- */
  /* Drag & drop                                                           */
  /* -------------------------------------------------------------------- */

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-dragover");
    });
  });

  ["dragleave", "dragend"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-dragover");
    });
  });

  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragover");
    const file = event.dataTransfer.files && event.dataTransfer.files[0];
    setFile(file);
  });

  /* -------------------------------------------------------------------- */
  /* Conversion                                                            */
  /* -------------------------------------------------------------------- */

  convertBtn.addEventListener("click", async () => {
    if (!currentFile) {
      showToast("Please choose a PDF file.", "error");
      return;
    }

    showPanel(panelLoading);

    const formData = new FormData();
    formData.append("file", currentFile);

    try {
      const response = await fetch("/convert", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Unable to convert this PDF.");
      }

      lastConvertedServerFilename = data.filename;
      downloadBtn.href = `/download/${encodeURIComponent(data.filename)}`;
      successFilename.textContent = `${currentFile.name.replace(/\.pdf$/i, "")}.docx is ready.`;
      showPanel(panelSuccess);
    } catch (error) {
      errorMessage.textContent = error.message || "Unable to convert this PDF.";
      showPanel(panelError);
    }
  });

  /* -------------------------------------------------------------------- */
  /* Download — branches on browser vs. desktop                           */
  /* -------------------------------------------------------------------- */

  downloadBtn.addEventListener("click", async (event) => {
    // Plain browser tab: let the <a download> link behave normally,
    // the browser saves it to its own download location.
    if (!isDesktopEnvironment()) {
      return;
    }

    // Desktop app: skip the browser download entirely and save the
    // file natively to the user's real Downloads folder instead.
    event.preventDefault();

    if (!lastConvertedServerFilename) {
      showDownloadErrorModal("No converted file is ready yet.");
      return;
    }

    const desiredName = currentFile
      ? `${currentFile.name.replace(/\.pdf$/i, "")}.docx`
      : lastConvertedServerFilename;

    try {
      const result = await window.pywebview.api.save_to_downloads(
        lastConvertedServerFilename,
        desiredName
      );

      if (result && result.success) {
        showDownloadSuccessModal(result);
      } else {
        showDownloadErrorModal((result && result.error) || "Unable to save the file.");
      }
    } catch (error) {
      showDownloadErrorModal(error.message || "Unable to save the file.");
    }
  });

  /* -------------------------------------------------------------------- */
  /* Desktop save modals                                                  */
  /* -------------------------------------------------------------------- */

  function showDownloadSuccessModal(result) {
    lastSavedFilePath = result.path;
    lastSavedFolderPath = result.folder;

    modalFilename.textContent = result.filename;
    modalLocation.textContent = friendlyFolderLabel(result.folder);

    downloadSuccessModal.hidden = false;
  }

  function showDownloadErrorModal(message) {
    modalErrorMessage.textContent = message;
    downloadErrorModal.hidden = false;
  }

  function friendlyFolderLabel(folderPath) {
    if (!folderPath) return "Downloads";
    const parts = folderPath.replace(/[\\/]+$/, "").split(/[\\/]/);
    return parts[parts.length - 1] || "Downloads";
  }

  modalOpenFileBtn.addEventListener("click", async () => {
    if (!lastSavedFilePath) return;
    const result = await window.pywebview.api.open_path(lastSavedFilePath);
    if (!result || !result.success) {
      showToast((result && result.error) || "Couldn't open the file.", "error");
    }
  });

  modalOpenFolderBtn.addEventListener("click", async () => {
    if (!lastSavedFolderPath) return;
    const result = await window.pywebview.api.open_path(lastSavedFolderPath);
    if (!result || !result.success) {
      showToast((result && result.error) || "Couldn't open the folder.", "error");
    }
  });

  modalConvertAnotherBtn.addEventListener("click", () => {
    downloadSuccessModal.hidden = true;
    resetToIdle();
  });

  modalErrorCloseBtn.addEventListener("click", () => {
    downloadErrorModal.hidden = true;
  });

  // Clicking the dimmed backdrop closes either modal, same as the
  // explicit buttons — a small, expected native-feeling affordance.
  [downloadSuccessModal, downloadErrorModal].forEach((overlay) => {
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) {
        overlay.hidden = true;
      }
    });
  });

  /* -------------------------------------------------------------------- */
  /* Resetting                                                             */
  /* -------------------------------------------------------------------- */

  function resetToIdle() {
    clearFile();
    lastConvertedServerFilename = null;
    lastSavedFilePath = null;
    lastSavedFolderPath = null;
    showPanel(panelIdle);
  }

  convertAnotherBtn.addEventListener("click", resetToIdle);
  tryAgainBtn.addEventListener("click", resetToIdle);

  /* -------------------------------------------------------------------- */
  /* Toasts                                                                */
  /* -------------------------------------------------------------------- */

  function showToast(message, variant) {
    const toast = document.createElement("div");
    toast.className = `toast${variant === "error" ? " toast--error" : ""}`;
    toast.textContent = message;
    toastStack.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3200);
  }
})();

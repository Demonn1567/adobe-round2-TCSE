import { useCallback, useState } from "react";
import { uploadFresh, uploadMany, uploadZip } from "../../lib/api.js";
import styles from "./UploadModal.module.css";
import FileUpload from "../svgicons/fileUploadIcon.jsx";

export default function UploadModal({ open, onClose, onOpened }) {
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const onPick = (list) => {
    const arr = Array.from(list || []);
    setFiles(arr);
    setMsg("");
    setErr("");
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    if (busy) return;
    onPick(e.dataTransfer?.files);
  }, [busy]);

  const onDrag = (e) => e.preventDefault();

  async function doUpload() {
    setErr("");
    setMsg("");
    if (!files.length) {
      setErr("Please choose PDF file(s) or a .zip.");
      return;
    }
    setBusy(true);
    try {
      let res;
      const onlyZip = files.length === 1 && /\.zip$/i.test(files[0].name);
      if (onlyZip) {
        res = await uploadZip(files[0]);
      } else if (files.length > 1) {
        res = await uploadMany(files);
      } else {
        const f = files[0];
        res = /\.zip$/i.test(f.name) ? await uploadZip(f) : await uploadFresh(f);
      }

      const docIds = Array.isArray(res?.docIds) ? res.docIds : [];
      if (docIds[0]) {
        sessionStorage.setItem("prism.lastFreshDocId", String(docIds[0]));
      }

      const firstPdf = files.find(f => /\.pdf$/i.test(f.name));
      if (firstPdf) {
        const blobUrl = URL.createObjectURL(firstPdf);
        sessionStorage.setItem("prism.lastFreshUrl", blobUrl);
        sessionStorage.setItem("prism.lastFreshName", firstPdf.name || "Document.pdf");
      }

      setMsg(
        docIds.length
          ? `Uploaded ${docIds.length} doc(s). You can start reading now.`
          : `Uploaded. Indexing has started.`
      );
      onOpened?.({ ok: true, docIds });

      setTimeout(() => onClose?.(), 500);
    } catch (e) {
      setErr(e?.message || "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) return null;

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
        onDrop={onDrop}
        onDragOver={onDrag}
        onDragEnter={onDrag}
      >
        <div className={styles.header}>
          <button className={styles.close} onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className={styles.uploadContainer}>
          <label className={styles.fileUpload}>
            <input
              type="file"
              multiple
              accept=".pdf,application/pdf,.zip,application/zip"
              onChange={(e) => onPick(e.target.files)}
            />
            <FileUpload dim={42} />
            <div className={styles.uploadText}>
              <span className={styles.largerSuggestion}>
                Drag and drop <span className={styles.highlightText}>Pdf file(s)</span> or a <span className={styles.highlightText}>.zip</span> here
              </span>
              <div>
                or <span className={styles.highlightText} style={{ textDecoration: "underline" }}>Browse file</span> on your computer
              </div>
            </div>
          </label>
        </div>

        {files.length > 0 && (
          <div className={styles.fileName}>
            {files.length === 1 ? files[0].name : `${files.length} files selected`}
          </div>
        )}

        <button
          className={styles.btn}
          style={{ opacity: busy ? 0.7 : 1, cursor: busy ? "wait" : "pointer" }}
          onClick={doUpload}
          disabled={busy}
        >
          {busy ? "Uploading…" : "Upload"}
        </button>

        {msg && <div className={styles.success}>{msg}</div>}
        {err && <div className={styles.error}>{err}</div>}
      </div>
    </div>
  );
}

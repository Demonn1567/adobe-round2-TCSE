import styles from "./Modal.module.css";

export default function Modal({ open, onClose, title, children, width = 720 }) {
  if (!open) return null;
  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div
        className={styles.sheet}
        style={{ maxWidth: width }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.header}>
          <div className={styles.title}>{title}</div>
          <button className={styles.close} onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className={styles.body}>{children}</div>
      </div>
    </div>
  );
}

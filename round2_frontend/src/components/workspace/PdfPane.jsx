import styles from "./PdfPane.module.css";


export default function PdfPane({ src }) {
  return (
    <div className={styles.wrap}>
      {src ? (
        <embed className={styles.viewer} src={src} type="application/pdf" />
      ) : (
        <div className={styles.placeholder}>
          <div className={styles.title}>Workspace</div>
          <div className={styles.desc}>
            Upload a PDF from Home or Library, then open it here.
            <br />
            Tip: paste a short snippet into the Ask box to ground answers.
          </div>
        </div>
      )}
    </div>
  );
}

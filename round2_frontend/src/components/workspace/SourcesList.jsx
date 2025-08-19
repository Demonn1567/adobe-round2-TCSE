import styles from "./SourcesList.module.css";

export default function SourcesList({ items = [] }) {
  if (!items.length) return <div className={styles.empty}>No sources yet.</div>;
  return (
    <div className={styles.list}>
      {items.map((s, i) => (
        <div key={`${s.sectionId || s.docId || i}-${i}`} className={styles.item}>
          <div className={styles.meta}>
            <div className={styles.title}>{s.docOrigName || s.docTitle || s.docId}</div>
            {typeof s.page === "number" && <div className={styles.page}>p.{s.page}</div>}
            {s.score != null && <div className={styles.score}>score {Number(s.score).toFixed(2)}</div>}
          </div>
          {s.snippet && <div className={styles.snippet}>{s.snippet}</div>}
        </div>
      ))}
    </div>
  );
}

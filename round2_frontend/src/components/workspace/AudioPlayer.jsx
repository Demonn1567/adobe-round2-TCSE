import styles from "./AudioPlayer.module.css";

export default function AudioPlayer({ src, downloadName = "answer.mp3" }) {
  return (
    <div className={styles.row}>
      <audio className={styles.audio} controls src={src} />
      <a className={styles.dl} href={src} download={downloadName}>Download</a>
    </div>
  );
}

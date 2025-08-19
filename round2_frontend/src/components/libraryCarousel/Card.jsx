import styles from "./LibraryCarousel.module.css";
import { useNavigate } from "react-router-dom";

export default function Card({ id }) {
  const nav = useNavigate();
  return (
    <div className={styles.card} onClick={() => nav("/workspace")}>
      <div className={styles.cardContent}>
        <div className={styles.cardDescription}>
          <div className={styles.cardTitle}>{"Random pdf".toUpperCase()}</div>
          <div className={styles.cardDate}>Sat Aug 16, 2025</div>
        </div>
        <div
          className={styles.cardImg}
          style={{ backgroundImage: `url(/src/assets/images/carousel/abstract-${id}.jpg)` }}
        />
      </div>
    </div>
  );
}

import styles from "./glassPdf.module.css"
import PdfIcon from "../svgicons/pdfIcon"
export default function GlassPdf(){
    return (
        <div className={styles.glassPdfs}>
            <div className={styles.glassCard}>
                <PdfIcon dim={45}/>
                <div className={styles.glassText}>PDF</div>
            </div>
        
            <div className={styles.behindGlass}>
                <div className={styles.behindClassContainer}>
                <PdfIcon dim={45}/>
                <div className={styles.glassText}>PDF</div>
                </div>
        </div>
    </div>
    )
}
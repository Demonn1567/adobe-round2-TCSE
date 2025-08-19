import styles from "./wiper.module.css"

export default function Wiper({index}){
    return (
        <div className={styles.wiper} style={{
            animationDelay: `${index*0.05}s`,
        }}>
        </div>
    )
}
import styles from "./Button.module.css"



export default function Button({color, bgColor, icon, btnText}){
    return (
        <button className={styles.btn} style={{"--clr-btn-bg": bgColor ? bgColor : "var(--clr-surface)", "--clr-btn": color ? color : "var(--clr-text-primary)"}}>
            {icon && <div className={styles.btnIcon}>icon</div>}
            <div className={styles.btnText}>{btnText}</div>
        </button>
    )
}
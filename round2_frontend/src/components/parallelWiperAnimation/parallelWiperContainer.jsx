import styles from "./parallelWiperContainer.module.css"
import Wiper from "./wiper";
const totalWipers = 20;


export default function parallelWiperContainer(){
    return (
        <div className={styles.wiperContainer} style={
            {
                display: "grid",
                gridTemplateColumns: `repeat(${totalWipers}, 1fr)`,
            }
        }>
            {Array(totalWipers).fill(0).map((_, index) => <Wiper index={index}/>)}

        </div>
    )
}
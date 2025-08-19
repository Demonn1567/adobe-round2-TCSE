
import styles from "./library.module.css"
import LibraryCarousel from "../libraryCarousel/LibraryCarousel"
export default function Library(){
    return (
           <div className={styles.library}>

                <LibraryCarousel/>
           </div>
    )
}
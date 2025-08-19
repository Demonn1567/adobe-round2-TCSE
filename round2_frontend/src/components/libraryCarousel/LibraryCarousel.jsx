import styles from "./LibraryCarousel.module.css"
import CarouselForwardIcon from "../svgicons/carouselForwardIcon"
import CarouselBackwardIcon from "../svgicons/carouselfBackwardIcon"
import SearchIcon from "../svgicons/searchIcon"
import { useRef, useState, useEffect } from "react"
import Card from "./Card"
import { GridIcon, StackedIcon } from "../svgicons/switchDisplay"



function Cards(){
    return Array(27).fill(0).map((_, index) => <Card id={(index)%9+1}/>)
}


export default function LibraryCarousel(){
    const [gridOrStack, setGirdOrStack] = useState("stack");
    const carouselContainer = useRef(null);
    const scrollVal = 400;


    function scroll(dir){
        const caros = carouselContainer.current;
        if(!caros) return;
        caros.scrollBy({
            left: dir * scrollVal,
            behavior: "smooth"
        });
    }

    function toggleDisplay(){
        if(gridOrStack === "stack"){
            setGirdOrStack("grid")
        }else{
            setGirdOrStack("stack")
        }

    }

    return (
        <div className={styles.mainContainer}>

            <div className={styles.topBar}>
                <div className={styles.libraryTitle}>
                    Library
                </div>
                <div className={styles.searchBar}>
                    <SearchIcon className={styles.searchIcon}/>
                    <input type="text"/>
                </div>
                {/* <div className={styles.switchCardPresentation}>
                    <div className={gridOrStack === "grid" ? styles.selected : ""} onClick={() => toggleDisplay()}><GridIcon/></div>
                    <div className={gridOrStack === "stack" ? styles.selected : ""} onClick={() => toggleDisplay()}><StackedIcon/></div>
                </div> */}
            </div>

            {gridOrStack === "stack" ? 
                <div className={styles.carouselContainer}>
                    <div className={`${styles.backArrow} ${styles.arrow}`} onClick={() => scroll(-1)}>
                        <CarouselBackwardIcon/>
                    </div>

                    <div className={styles.cardContainer}  ref={carouselContainer}>
                        <Cards/>
                    </div>

                    <div className={`${styles.forwardArrow} ${styles.arrow}`}  onClick={() => scroll(1)}>
                        <CarouselForwardIcon/>
                    </div>
                </div>
            :
                <div className={styles.gridOfCards}>
                    <Cards/>
                </div>
            }         

        </div>
    )
}
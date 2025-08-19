import React, { useRef, useState, useEffect } from 'react';
import styles from './Carousel.module.css';

const Carousel = () => {
    const cardContainerRef = useRef(null);
    const [isBackDisabled, setIsBackDisabled] = useState(true);
    const [isForwardDisabled, setIsForwardDisabled] = useState(false);

    const totalCards = 9;
    const cards = Array.from({ length: totalCards }, (_, i) => i + 1);
    const handleScroll = () => {
        const container = cardContainerRef.current;
        if (container) {
            const atStart = container.scrollLeft === 0;
            const atEnd = container.scrollWidth - container.clientWidth - container.scrollLeft < 1;
            setIsBackDisabled(atStart);
            setIsForwardDisabled(atEnd);
        }
    };

    useEffect(() => {
        const container = cardContainerRef.current;
        if (container) {
            if (container.scrollWidth <= container.clientWidth) {
                setIsForwardDisabled(true);
            }
            container.addEventListener('scroll', handleScroll);
            return () => container.removeEventListener('scroll', handleScroll);
        }
    }, []);

    const scroll = (direction) => {
        const container = cardContainerRef.current;
        if (container) {
            const scrollAmount = 300; 
            container.scrollBy({
                left: direction === 'forward' ? scrollAmount : -scrollAmount,
                behavior: 'smooth',
            });
        }
    };

    return (
        <div className={styles.mainContainer}>
            <div
                className={`${styles.arrow} ${styles.backArrow} ${isBackDisabled ? styles.disabled : ''}`}
                onClick={() => !isBackDisabled && scroll('backward')}
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m15 18-6-6 6-6"/>
                </svg>
            </div>

            <div className={styles.cardContainer} ref={cardContainerRef}>
                {cards.map(id => (
                    <div key={id} className={styles.card}>
                        <div className={styles.cardContent}>
                            <div className={styles.cardDescription}>
                                <div className={styles.cardTitle}>
                                    PDF TITLE
                                </div>
                                <div className={styles.cardDate}>
                                    Sat Aug 16, 2025
                                </div>
                            </div>
                            <div
                                className={styles.cardImg}
                                style={{ backgroundImage: `url('../../assets/images/carousel/abstract-${id}.jpg')` }}
                            >
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div
                className={`${styles.arrow} ${styles.forwardArrow} ${isForwardDisabled ? styles.disabled : ''}`}
                onClick={() => !isForwardDisabled && scroll('forward')}
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m9 18 6-6-6-6"/>
                </svg>
            </div>
        </div>
    );
};

export default Carousel;






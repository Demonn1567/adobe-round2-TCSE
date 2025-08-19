import { useEffect, useRef, useState } from "react";
import styles from "./glassLoading.module.css";

function GlassBone({ containerWidth }) {
  const randomWidth = Math.floor(
    Math.random() * (containerWidth * 0.75 - containerWidth * 0.20) +
      containerWidth * 0.20
  );

  return (
    <div
      className={styles.glassBone}
      style={{
        width: `${randomWidth}px`,
      }}
    />
  );
}

export default function GlassLoading({ loaderCount }) {
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    if (containerRef.current) {
      setContainerWidth(containerRef.current.offsetWidth);
    }

    // const handleResize = () => {
    //   if (containerRef.current) {
    //     setContainerWidth(containerRef.current.offsetWidth);
    //   }
    // };
    // window.addEventListener("resize", handleResize);

    // return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className={styles.glassSkeleton} ref={containerRef}>
      {containerWidth > 0 &&
        Array.from({ length: loaderCount }).map((_, i) => (
          <GlassBone key={i} containerWidth={containerWidth} />
        ))}
    </div>
  );
}

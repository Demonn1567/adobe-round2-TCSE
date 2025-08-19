import styles from "./Hero.module.css";
import Button from "../button/Button";

import hotAirBaloonDark from "../../assets/images/darkHero/hotAirBaloon.webp";
import skylineDark from "../../assets/images/darkHero/skyline.webp";
import cloudDark from "../../assets/images/darkHero/cloud1.webp";
import cloudAtBackDark from "../../assets/images/darkHero/cloudback.webp";
import moon from "../../assets/images/darkHero/mooon.webp";

import hotAirBaloonLight from "../../assets/images/lightHero/hotAirBaloon.webp";
import skylineLight from "../../assets/images/lightHero/skyline.webp";
import cloudLight from "../../assets/images/lightHero/cloud1.webp";
import cloudAtBackLight from "../../assets/images/lightHero/cloudback.webp";
import sun from "../../assets/images/lightHero/mooon.webp";

import { useState } from "react";
import UploadModal from "../modals/UploadModal.jsx";
import DemoModal from "../modals/DemoModal.jsx";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../ThemeContext";


function HeroText({ children, highlight, color, from, to }) {
  if (!highlight) return children;
  const words = children.split(" ");
  return (
    <div>
      {words.map((word, index) => {
        if (index >= from && index <= to) {
          return (
            <span key={index} style={{ color: color || "hsla(var(--clr-surface))" }}>
              {word}{" "}
            </span>
          );
        }
        return word + " ";
      })}
    </div>
  );
}

function HeroIllus() {
  const { theme: themeSelected } = useTheme();

  if (themeSelected === "dark") {
    return (
      <div className={styles.heroIllus}>
        <img src={hotAirBaloonDark} alt="" className={`${styles.hotAirBaloon} ${styles.heroImg}`} />
        <img src={skylineDark} alt="" className={`${styles.skyline} ${styles.heroImg}`} />
        <img src={cloudDark} alt="" className={`${styles.cloud} ${styles.heroImg}`} />
        <img src={cloudDark} alt="" className={`${styles.cloud2} ${styles.heroImg}`} />
        <img src={cloudAtBackDark} alt="" className={`${styles.cloud2} ${styles.heroImg}`} />
        <img src={moon} alt="" className={`${styles.moon} ${styles.heroImg}`} />
      </div>
    );
  }

  return (
    <div className={styles.heroIllus}>
      <img src={hotAirBaloonLight} alt="" className={`${styles.hotAirBaloon} ${styles.heroImg}`} />
      <img src={skylineLight} alt="" className={`${styles.skyline} ${styles.heroImg}`} />
      <img src={cloudLight} alt="" className={`${styles.cloud} ${styles.heroImg}`} />
      <img src={cloudLight} alt="" className={`${styles.cloud2} ${styles.heroImg}`} />
      <img src={cloudAtBackLight} alt="" className={`${styles.cloud2} ${styles.heroImg}`} />
      <img src={sun} alt="" className={`${styles.moon} ${styles.heroImg}`} />
    </div>
  );
}


export default function Hero() {
  const [openUpload, setOpenUpload] = useState(false);
  const [openDemo, setOpenDemo] = useState(false);
  const nav = useNavigate();

  return (
    <div className={styles.heroContainer}>
      <div className={styles.heroContent}>
        <div className={styles.heading}>
          <div>{"Beyond the Page.".toUpperCase()}</div>
          <HeroText highlight={true} from={1} to={1}>
            {"Deeper Insights.".toUpperCase()}
          </HeroText>
        </div>

        <div className={styles.subHeading}>
          Prism connects the dots across your documents, revealing hidden knowledge and accelerating your research.
        </div>

        <div className={styles.ctaBtns}>
          <div onClick={() => setOpenUpload(true)}>
            <Button btnText={"Start a New Session"} bgColor={"205, 91%, 65%"} />
          </div>
          <div onClick={() => setOpenDemo(true)}>
            <Button btnText={"Watch Demo"} />
          </div>
        </div>
      </div>

      <HeroIllus />

      <UploadModal
        open={openUpload}
        onClose={() => setOpenUpload(false)}
        onReady={() => nav("/workspace")}
      />
      <DemoModal open={openDemo} onClose={() => setOpenDemo(false)} />
    </div>
  );
}

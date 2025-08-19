import styles from "./Navbar.module.css";
import Button from "../button/Button";
import { Link, useLocation } from "react-router-dom";
import { useTheme } from "../../ThemeContext";
import LightThemeIcon from "../svgicons/lightThemeIcon";
import DarkThemeIcon from "../svgicons/darkThemeIcon";
import LogoIcon from "../svgicons/logoIcon";

function ToggleTheme({ themeSelected, setThemeSelected }) {
  return (
    <div className={styles.toggleTheme}>
      <div
        className={`${styles.lightTheme} ${
          themeSelected === "light" ? styles.selected : ""
        }`}
        onClick={() => setThemeSelected("light")}
      >
        <LightThemeIcon />
      </div>
      <div
        className={`${styles.darkTheme} ${
          themeSelected === "dark" ? styles.selected : ""
        }`}
        onClick={() => setThemeSelected("dark")}
      >
        <DarkThemeIcon />
      </div>
    </div>
  );
}

const navItemsArr = [
  { name: "Home", path: "/" },
  { name: "Library", path: "/library" },
  { name: "Workspace", path: "/workspace" },
];

export default function Navbar() {
  const { theme: themeSelected, setTheme: setThemeSelected } = useTheme();
  const location = useLocation(); 

  return (
    <nav className={styles.navbar}>
      <div className={styles.logoBit}>
        <LogoIcon dim={30} />
        <div className={`${styles.navItem} ${styles.logo}`}>PRISM</div>
      </div>

      <div className={styles.pageRoutes}>
        {navItemsArr.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={!isActive ? styles.navItem : ""}
            >
              {isActive ? <Button btnText={item.name} /> : item.name}
            </Link>
          );
        })}
      </div>

      <div className={styles.pageCtrls}>
        <ToggleTheme
          themeSelected={themeSelected}
          setThemeSelected={setThemeSelected}
        />
      </div>
    </nav>
  );
}

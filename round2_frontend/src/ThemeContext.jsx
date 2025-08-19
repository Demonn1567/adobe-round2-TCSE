import { createContext, useEffect, useState, useContext } from "react";


const ThemeContext = createContext();


export const ThemeProvider = ({children}) => {
    const [theme, setTheme] = useState("dark");

    useEffect(() => {
        const root = window.document.documentElement;
        console.log("theme changed!!!")
        if (theme === 'dark') {
          root.removeAttribute('data-theme');
        } else {
          root.setAttribute('data-theme', 'light');
        }
      }, [theme]);

      const value = { theme, setTheme };

      return (
        <ThemeContext.Provider value={value}>
          {children}
        </ThemeContext.Provider>
      );

}

export const useTheme = () => {
    return useContext(ThemeContext);
  };
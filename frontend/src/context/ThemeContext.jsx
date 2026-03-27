import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

function readTheme() {
  try {
    return localStorage.getItem('glanceos-theme') || 'dark';
  } catch {
    return 'dark';
  }
}

function writeTheme(theme) {
  try {
    localStorage.setItem('glanceos-theme', theme);
  } catch {
    // Ignore storage failures in restricted browser contexts.
  }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    writeTheme(theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => (t === 'dark' ? 'light' : 'dark'));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

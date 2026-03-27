import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();
const THEME_PREFERENCE_KEY = 'glanceos-theme-preference';
const LEGACY_THEME_KEY = 'glanceos-theme';

function scheduledTheme(date = new Date()) {
  const hour = date.getHours();
  // 10:00-16:59 light, 17:00-09:59 dark.
  return hour >= 10 && hour < 17 ? 'light' : 'dark';
}

function normalizePreference(value) {
  if (value === 'light' || value === 'dark' || value === 'auto') return value;
  return null;
}

function readTheme() {
  try {
    const pref = normalizePreference(localStorage.getItem(THEME_PREFERENCE_KEY));
    if (pref) return pref;

    // Backward compatibility with legacy key from older builds.
    const legacy = normalizePreference(localStorage.getItem(LEGACY_THEME_KEY));
    if (legacy === 'light' || legacy === 'dark') return legacy;

    return 'auto';
  } catch {
    return 'auto';
  }
}

function writeThemePreference(themePreference) {
  try {
    localStorage.setItem(THEME_PREFERENCE_KEY, themePreference);

    // Keep legacy key updated for compatibility with older code paths.
    if (themePreference === 'light' || themePreference === 'dark') {
      localStorage.setItem(LEGACY_THEME_KEY, themePreference);
    }
  } catch {
    // Ignore storage failures in restricted browser contexts.
  }
}

export function ThemeProvider({ children }) {
  const [themePreference, setThemePreference] = useState(readTheme);
  const [theme, setTheme] = useState(() => {
    const preference = readTheme();
    return preference === 'auto' ? scheduledTheme() : preference;
  });

  useEffect(() => {
    writeThemePreference(themePreference);
  }, [themePreference]);

  useEffect(() => {
    const applyTheme = () => {
      const nextTheme = themePreference === 'auto' ? scheduledTheme() : themePreference;
      setTheme(nextTheme);
      document.documentElement.setAttribute('data-theme', nextTheme);
    };

    applyTheme();

    if (themePreference !== 'auto') return;

    const intervalId = setInterval(applyTheme, 60_000);
    return () => clearInterval(intervalId);
  }, [themePreference]);

  const toggleTheme = () => {
    setThemePreference(prev => {
      if (prev === 'auto') return 'light';
      if (prev === 'light') return 'dark';
      return 'auto';
    });
  };

  return (
    <ThemeContext.Provider value={{ theme, themePreference, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

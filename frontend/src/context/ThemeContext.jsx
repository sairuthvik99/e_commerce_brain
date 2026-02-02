import { createContext, useContext, useState, useEffect, useCallback } from 'react';

// Theme modes
export const THEME_MODES = {
  LIGHT: 'light',
  DARK: 'dark'
};

// Create context
const ThemeContext = createContext(null);

/**
 * Theme Provider Component
 * Manages dark/light mode (STEB's UI only)
 */
export function ThemeProvider({ children }) {
  const [themeMode, setThemeMode] = useState(() => {
    const saved = localStorage.getItem('stebs-theme-mode');
    if (saved && Object.values(THEME_MODES).includes(saved)) {
      return saved;
    }
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return THEME_MODES.DARK;
    }
    return THEME_MODES.LIGHT;
  });

  useEffect(() => {
    localStorage.setItem('stebs-theme-mode', themeMode);
  }, [themeMode]);

  // Apply theme classes to document
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove all theme classes
    root.classList.remove('theme-light', 'theme-dark');
    
    // Add current theme classes (always STEB's UI)
    root.classList.add(`theme-${themeMode}`);
    root.classList.add('ui-stebs');
    
    // Set data attributes for CSS selectors
    root.setAttribute('data-theme', themeMode);
    root.setAttribute('data-ui', 'stebs');
  }, [themeMode]);

  // Toggle dark/light mode
  const toggleThemeMode = useCallback(() => {
    setThemeMode(prev => 
      prev === THEME_MODES.LIGHT ? THEME_MODES.DARK : THEME_MODES.LIGHT
    );
  }, []);

  // Check if dark mode
  const isDarkMode = themeMode === THEME_MODES.DARK;

  const value = {
    themeMode,
    setThemeMode,
    toggleThemeMode,
    isDarkMode,
    THEME_MODES
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Hook to use theme context
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export default ThemeContext;

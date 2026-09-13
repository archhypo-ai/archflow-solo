import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import { AppSettings } from "../settings/AppSettings";
import type { AppearancePreference } from "../settings/types";

export type Theme = "dark" | "light";

type ThemeContextValue = {
  theme: Theme;
  appearance: AppearancePreference;
  setAppearance: (appearance: AppearancePreference) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getSystemTheme(): Theme {
  if (typeof window === "undefined" || !window.matchMedia) return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function ThemeProvider({ children }: PropsWithChildren) {
  const [appearance, setAppearanceState] =
    useState<AppearancePreference>("system");
  const [systemTheme, setSystemTheme] = useState<Theme>(getSystemTheme);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    void AppSettings.getOrDefault("appearance").then((stored) => {
      if (!active) return;
      setAppearanceState(stored);
      setSettingsLoaded(true);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (event: MediaQueryListEvent) =>
      setSystemTheme(event.matches ? "dark" : "light");
    setSystemTheme(mediaQuery.matches ? "dark" : "light");
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const theme = appearance === "system" ? systemTheme : appearance;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const setAppearance = useCallback((nextAppearance: AppearancePreference) => {
    setAppearanceState(nextAppearance);
  }, []);

  useEffect(() => {
    if (settingsLoaded) void AppSettings.set("appearance", appearance);
  }, [appearance, settingsLoaded]);

  const toggleTheme = useCallback(() => {
    setAppearanceState((current) => (current === "dark" ? "light" : "dark"));
  }, []);

  const value = useMemo(
    () => ({ appearance, setAppearance, theme, toggleTheme }),
    [appearance, setAppearance, theme, toggleTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used inside ThemeProvider");
  return context;
}

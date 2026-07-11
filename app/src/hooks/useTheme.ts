import { useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";
const KEY = "bbtm.theme";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem(KEY) as Theme) || "system");

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    localStorage.setItem(KEY, theme);
  }, [theme]);

  const cycle = () => setTheme((t) => (t === "light" ? "dark" : t === "dark" ? "system" : "light"));
  return { theme, setTheme, cycle };
}

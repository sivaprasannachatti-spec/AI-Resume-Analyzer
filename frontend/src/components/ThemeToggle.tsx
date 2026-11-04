"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    try {
      const shouldBeDark = document.documentElement.dataset.theme === "dark";
      setIsDark(shouldBeDark);
    } catch (error) {
      console.error("Unable to read theme preference", error);
    }
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    document.documentElement.dataset.theme = nextDark ? "dark" : "light";
    document.documentElement.classList.toggle("dark", nextDark);
    try {
      localStorage.setItem("theme", nextDark ? "dark" : "light");
    } catch (error) {
      console.error("Unable to persist theme preference", error);
    }
  };

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className="relative flex h-9 w-[4.25rem] items-center justify-between rounded-full border border-slate-200/80 bg-white/70 px-1.5 text-slate-600 shadow-sm transition-all duration-300 hover:scale-105 active:scale-95 dark:border-white/10 dark:bg-slate-800/80 dark:text-slate-200"
    >
      <Sun className="z-10 h-3.5 w-3.5 text-amber-600 dark:text-amber-300" />
      <Moon className="z-10 h-3.5 w-3.5 text-indigo-500 dark:text-indigo-200" />
      <span
        aria-hidden="true"
        className={`absolute h-7 w-7 rounded-full bg-white shadow-sm transition-transform duration-300 dark:bg-slate-700 ${
          isDark ? "translate-x-7" : "translate-x-0"
        }`}
      />
    </button>
  );
}

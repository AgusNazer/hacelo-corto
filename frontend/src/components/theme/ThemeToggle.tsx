"use client";

import { MoonStar, SunMedium } from "lucide-react";
import { useTheme } from "@/src/components/theme/ThemeProvider";

type ThemeToggleProps = {
  compact?: boolean;
};

export function ThemeToggle({ compact = false }: ThemeToggleProps) {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm font-semibold text-white/85 transition hover:bg-white/10 ${
        compact ? "h-10" : ""
      }`}
      aria-label={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      title={isDark ? "Modo claro" : "Modo oscuro"}
    >
      {isDark ? <SunMedium size={16} /> : <MoonStar size={16} />}
      {!compact ? <span>{isDark ? "Claro" : "Oscuro"}</span> : null}
    </button>
  );
}

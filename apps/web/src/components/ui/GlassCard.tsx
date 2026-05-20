"use client";

import { cn } from "@/lib/utils";
import { useTheme } from "@/context/ThemeContext";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  glowColor?: string;
  hover?: boolean;
}

export default function GlassCard({
  children,
  className,
  glow = false,
  glowColor,
  hover = false,
}: GlassCardProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div
      className={cn(
        "border rounded-xl transition-colors duration-300",
        glow && "[box-shadow:0_1px_3px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04)]",
        hover && "transition-all duration-300 hover:-translate-y-1",
        className
      )}
      style={{
        background: isDark ? "#141210" : "#FFFFFF",
        borderColor: isDark ? "#2E2922" : "#EAEAEC",
        ...(hover ? { boxShadow: isDark ? "0 1px 3px rgba(0,0,0,0.3)" : "0 1px 3px rgba(0,0,0,0.06)" } : {}),
        ...(glowColor ? { boxShadow: `0 0 40px ${glowColor}` } : {}),
      }}
    >
      {children}
    </div>
  );
}

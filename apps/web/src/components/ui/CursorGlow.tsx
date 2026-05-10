"use client";
import { useEffect, useRef } from "react";
import { useTheme } from "@/context/ThemeContext";

export default function CursorGlow() {
  const glowRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    let frameId: number | null = null;
    const h = (e: MouseEvent) => {
      if (frameId !== null) return;
      frameId = requestAnimationFrame(() => {
        if (glowRef.current) {
          glowRef.current.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0)`;
        }
        frameId = null;
      });
    };
    window.addEventListener("mousemove", h, { passive: true });
    return () => {
      window.removeEventListener("mousemove", h);
      if (frameId !== null) cancelAnimationFrame(frameId);
    };
  }, []);

  const isDark = theme === "dark";
  const glowColor = isDark ? "rgba(196, 168, 130, 0.05)" : "rgba(163, 138, 112, 0.06)";

  return (
    <div
      ref={glowRef}
      aria-hidden="true"
      className="fixed pointer-events-none z-[9998] will-change-transform"
      style={{
        left: "-700px",
        top: "-700px",
        width: "1400px",
        height: "1400px",
        background: `radial-gradient(circle closest-side, ${glowColor}, transparent)`,
      }}
    />
  );
}

"use client";
import { useEffect } from "react";
export default function CursorGlow() {
  useEffect(() => {
    const h = (e: MouseEvent) => {
      document.documentElement.style.setProperty("--cx", `${e.clientX}px`);
      document.documentElement.style.setProperty("--cy", `${e.clientY}px`);
    };
    window.addEventListener("mousemove", h);
    return () => window.removeEventListener("mousemove", h);
  }, []);
  return null;
}

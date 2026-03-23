import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "#030407",
        surface: {
          1: "#07080f",
          2: "#0c0d1a",
          3: "#111328",
        },
        accent: {
          violet: "#6c47ff",
          cyan: "#00d4ff",
          amber: "#f59e0b",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "glow-sm": "0 0 20px rgba(108,71,255,0.2)",
        "glow": "0 0 40px rgba(108,71,255,0.25)",
        "glow-lg": "0 0 80px rgba(108,71,255,0.2)",
        "glow-cyan": "0 0 40px rgba(0,212,255,0.2)",
        "card": "0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06)",
        "card-hover": "0 40px 100px rgba(0,0,0,0.7), 0 0 0 1px rgba(108,71,255,0.2)",
      },
      animation: {
        "float": "float-1 4s ease-in-out infinite",
        "float-slow": "float-2 6s ease-in-out infinite",
        "spin-slow": "spin-slow 12s linear infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4,0,0.6,1) infinite",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "aurora": "linear-gradient(135deg, #6c47ff 0%, #00d4ff 100%)",
      },
    },
  },
  plugins: [],
};

export default config;

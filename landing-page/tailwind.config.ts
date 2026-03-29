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
        base: "#F9F8F6",
        surface: {
          1: "#F5F5F4",
          2: "#FFFFFF",
          3: "#EAEAEC",
        },
        onyx: "#0F172A",
        brand: "#0F172A",
        accent: {
          bronze: "#A38A70",
          olive: "#7A8B76",
          onyx: "#0F172A",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "glow-sm": "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "glow": "0 4px 16px rgba(0,0,0,0.08)",
        "glow-lg": "0 8px 30px rgba(0,0,0,0.10)",
        "glow-bronze": "0 4px 16px rgba(163,138,112,0.12)",
        "card": "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "card-hover": "0 20px 40px -10px rgba(0,0,0,0.04)",
        "lift": "0 4px 20px rgba(0,0,0,0.10), 0 1px 3px rgba(0,0,0,0.08)",
      },
      animation: {
        "float": "float-1 4s ease-in-out infinite",
        "float-slow": "float-2 6s ease-in-out infinite",
        "spin-slow": "spin-slow 12s linear infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4,0,0.6,1) infinite",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "aurora": "linear-gradient(135deg, #A38A70 0%, #0F172A 100%)",
      },
    },
  },
  plugins: [],
};

export default config;

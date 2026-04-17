import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#030712",
        ink: "#f8fafc",
        coral: "#f43f5e",
        mint: "#10b981",
        amber: "#fbbf24",
      },
      fontFamily: {
        display: ["Outfit", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -10px var(--tw-shadow-color)",
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.3)",
        focus: "0 0 0 2px var(--bg-1), 0 0 0 4px var(--accent-1)",
      },
      zIndex: {
        '10': '10',
        '20': '20',
        '30': '30',
        '40': '40',
        '50': '50',
      }
    },
  },
  plugins: [],
};

export default config;

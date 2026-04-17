import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F8FAFC",
        ink: "#1E293B",
        primary: "#3B82F6",
        secondary: "#60A5FA",
        cta: "#F97316",
        border: "#E2E8F0",
      },
      fontFamily: {
        display: ["Righteous", "sans-serif"],
        body: ["Poppins", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px -5px var(--tw-shadow-color)",
        block: "4px 4px 0px 0px rgba(30, 41, 59, 1)",
        'block-hover': "6px 6px 0px 0px rgba(30, 41, 59, 1)",
        focus: "0 0 0 2px var(--bg-1), 0 0 0 4px var(--primary)",
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

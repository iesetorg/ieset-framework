import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#ffffff",
        ink: "#1f1f1f",
        muted: "#636363",
        faint: "#8a8a8a",
        rule: "#ececec",
        "rule-strong": "#d9d9d9",
        panel: "#fafaf8",
        "code-bg": "#f3f3f1",
        accent: "#1f4e79",
        "accent-soft": "#e1ecf5",
        green: "#2c7a4f",
        "green-soft": "#dff1e4",
        amber: "#b7791f",
        "amber-soft": "#fdf1da",
        red: "#9e2f2f",
        "red-soft": "#f3d9d9",
        series: {
          1: "#4E79A7",
          2: "#59A14F",
          3: "#B07AA1",
          4: "#E15759",
          5: "#F28E2B",
          6: "#76B7B2",
          7: "#EDC948",
          8: "#B6992D",
          9: "#9C755F",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Inter",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ['"SF Mono"', "Menlo", "Consolas", "monospace"],
      },
      fontSize: {
        "sc": ["11px", { lineHeight: "1.4", letterSpacing: "0.1em" }],
      },
      maxWidth: {
        content: "1120px",
      },
    },
  },
  plugins: [],
};

export default config;

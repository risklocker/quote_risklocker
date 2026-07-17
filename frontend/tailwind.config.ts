import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-vietnam)", "Arial", "sans-serif"]
      },
      colors: {
        rl: {
          text: "var(--color-text-primary)",
          textStrong: "var(--color-text-secondary)",
          inverse: "var(--color-text-tertiary)",
          red: "var(--color-surface-muted)",
          black: "var(--color-surface-base)",
          blue: "var(--color-surface-strong)",
          line: "var(--color-line)",
          soft: "var(--color-soft)",
          warning: "var(--color-warning)",
          success: "var(--color-success)"
        }
      },
      boxShadow: {
        focus: "0 0 0 3px rgba(0, 132, 255, 0.22)"
      }
    }
  },
  plugins: []
};

export default config;

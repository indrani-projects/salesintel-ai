/** @type {import('tailwindcss').Config} */
// Direction C — Product Workspace palette. See mockups/C-workspace.html.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Page + surfaces
        bg: "#eef1f6",
        panel: "#ffffff",

        // Primary accent (indigo) — retuned brand scale so all `brand-*`
        // utilities land on the Direction C indigo. brand-600 == accent.
        brand: {
          50: "#ecedfb", // accent-soft
          100: "#dfe0f8",
          200: "#c7c8f3",
          300: "#a6a8ec",
          400: "#7a7ce4",
          500: "#5457d6",
          600: "#3538cd", // --accent
          700: "#2c2eb0",
          800: "#262894",
          900: "#23246f",
        },

        // Neutral ink scale retuned to the Direction C greys.
        ink: {
          50: "#f7f8fc",
          100: "#eef1f6", // --line2
          200: "#e5e9f0", // --line
          300: "#d2d8e3",
          400: "#8a93a6", // --faint
          500: "#5a6478", // --muted
          600: "#464f63",
          700: "#333c4e",
          800: "#222a3a",
          900: "#111726", // --ink
          950: "#0b1020",
        },

        // Named tokens (mirror the mockup CSS vars)
        accent: { DEFAULT: "#3538cd", soft: "#ecedfb" },
        line: "#e5e9f0",
        line2: "#eef1f6",
        faint: "#8a93a6",
        muted: "#5a6478",
        nav: { DEFAULT: "#141a2e", ink: "#c4cbdb" },

        // Semantic
        good: "#0f9d58",
        warn: "#c07d12",
        bad: "#d33a4b",
      },
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(17, 23, 38, 0.03), 0 6px 20px -8px rgba(17, 23, 38, 0.08)",
        "card-hover":
          "0 2px 4px 0 rgba(17, 23, 38, 0.05), 0 14px 30px -10px rgba(53, 56, 205, 0.16)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
};

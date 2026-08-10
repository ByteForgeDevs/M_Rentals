/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./apps/**/*.py", "./apps/**/*.html"],
  theme: {
    extend: {
      colors: {
        // Brand guidelines v1.0: the mark stays black, green is the accent.
        brand: {
          DEFAULT: "#1B9D80",
          50: "#EEFAF6",
          100: "#D2F2E9",
          200: "#A6E5D4",
          300: "#6FD3BA",
          400: "#3BB89B",
          500: "#1B9D80",
          600: "#157E67",
          700: "#12634F",
          800: "#0F4E40",
          900: "#0B3B30",
        },
        ink: "#000000",
        // Warm neutral for large surfaces. Pure slate reads cold behind listing
        // photos, which sit on these surfaces on every page.
        canvas: {
          50: "#FAFAF9",
          100: "#F5F5F3",
          200: "#E9E9E5",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "Helvetica Neue",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      letterSpacing: {
        wordmark: "0.18em",
      },
      fontSize: {
        // Display sizes pair large type with tight leading so a long headline
        // holds together as one block instead of drifting apart.
        "display-sm": ["2.25rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        display: ["2.75rem", { lineHeight: "1.06", letterSpacing: "-0.025em" }],
        "display-lg": ["3.5rem", { lineHeight: "1.02", letterSpacing: "-0.03em" }],
      },
      borderRadius: {
        "4xl": "1.75rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.06), 0 8px 24px -12px rgba(15, 23, 42, 0.18)",
        lift: "0 2px 4px rgba(15, 23, 42, 0.06), 0 18px 40px -18px rgba(15, 23, 42, 0.28)",
        panel: "0 24px 60px -24px rgba(15, 23, 42, 0.35)",
      },
      transitionTimingFunction: {
        "out-soft": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "rise-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 200ms ease-out both",
        "rise-in": "rise-in 260ms cubic-bezier(0.22, 1, 0.36, 1) both",
      },
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};

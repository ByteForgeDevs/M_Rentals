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
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.06), 0 8px 24px -12px rgba(15, 23, 42, 0.18)",
      },
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};

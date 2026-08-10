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
        "5xl": "2.5rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.06), 0 8px 24px -12px rgba(15, 23, 42, 0.18)",
        lift: "0 2px 4px rgba(15, 23, 42, 0.06), 0 18px 40px -18px rgba(15, 23, 42, 0.28)",
        panel: "0 24px 60px -24px rgba(15, 23, 42, 0.35)",
        // A tall, soft shadow reads as real elevation rather than a grey outline.
        float: "0 4px 8px -4px rgba(15, 23, 42, 0.08), 0 32px 64px -24px rgba(15, 23, 42, 0.34)",
        // Green light under the primary button ties it to the brand.
        glow: "0 8px 24px -8px rgba(27, 157, 128, 0.45)",
        "glow-lg": "0 14px 40px -10px rgba(27, 157, 128, 0.5)",
        "inner-top": "inset 0 1px 0 0 rgba(255, 255, 255, 0.08)",
      },
      transitionTimingFunction: {
        "out-soft": "cubic-bezier(0.22, 1, 0.36, 1)",
        // Overshoots slightly, which makes a control feel physical when it lands.
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
      transitionDuration: {
        400: "400ms",
        600: "600ms",
      },
      backgroundImage: {
        // Two offset radial washes read as depth without needing an image.
        "mesh-brand":
          "radial-gradient(60% 60% at 12% 0%, rgba(27,157,128,0.13) 0%, rgba(27,157,128,0) 100%), radial-gradient(50% 55% at 92% 18%, rgba(59,184,155,0.16) 0%, rgba(59,184,155,0) 100%)",
        "mesh-dark":
          "radial-gradient(55% 55% at 85% 0%, rgba(27,157,128,0.32) 0%, rgba(27,157,128,0) 100%), radial-gradient(45% 60% at 8% 100%, rgba(27,157,128,0.18) 0%, rgba(27,157,128,0) 100%)",
        "grid-slate":
          "linear-gradient(to right, rgba(15,23,42,0.045) 1px, transparent 1px), linear-gradient(to bottom, rgba(15,23,42,0.045) 1px, transparent 1px)",
        "fade-up-white":
          "linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,1) 100%)",
        shimmer:
          "linear-gradient(90deg, rgba(226,232,240,0) 0%, rgba(255,255,255,0.85) 50%, rgba(226,232,240,0) 100%)",
      },
      backgroundSize: {
        grid: "44px 44px",
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
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(100%)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        // Ambient drift for the hero washes. Slow enough to never pull the eye.
        float: {
          "0%, 100%": { transform: "translate3d(0, 0, 0) scale(1)" },
          "50%": { transform: "translate3d(0, -18px, 0) scale(1.06)" },
        },
        shimmer: {
          from: { transform: "translateX(-100%)" },
          to: { transform: "translateX(100%)" },
        },
        // A single soft pulse, used to draw the eye to a live count.
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "70%": { transform: "scale(1.6)", opacity: "0" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
      },
      animation: {
        "fade-in": "fade-in 200ms ease-out both",
        "rise-in": "rise-in 260ms cubic-bezier(0.22, 1, 0.36, 1) both",
        "scale-in": "scale-in 220ms cubic-bezier(0.22, 1, 0.36, 1) both",
        "slide-up": "slide-up 320ms cubic-bezier(0.22, 1, 0.36, 1) both",
        float: "float 14s ease-in-out infinite",
        "float-slow": "float 22s ease-in-out infinite",
        shimmer: "shimmer 1.8s ease-in-out infinite",
        "pulse-ring": "pulse-ring 2.4s cubic-bezier(0.22, 1, 0.36, 1) infinite",
      },
    },
  },
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography")],
};

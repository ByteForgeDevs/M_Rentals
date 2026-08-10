/** @type {import('tailwindcss').Config} */

// Neutral, canvas, surface and brand are declared as channel triplets in
// `assets/css/input.css` and read back here through `rgb(var(--x) / <alpha-value>)`.
// That indirection is what makes dark mode a variable swap on <html> rather than
// a `dark:` variant on several hundred utilities across the templates.
const withVar = (name) => `rgb(var(${name}) / <alpha-value>)`;

const ramp = (prefix, shades) =>
  Object.fromEntries(shades.map((shade) => [shade, withVar(`--${prefix}-${shade}`)]));

module.exports = {
  darkMode: "class",
  content: ["./templates/**/*.html", "./apps/**/*.py", "./apps/**/*.html"],
  theme: {
    extend: {
      colors: {
        // Brand guidelines v1.0: the mark stays black, green is the accent.
        // The tint end of the ramp doubles as a surface, so it has to invert in
        // dark mode or every badge turns into a bright patch.
        brand: {
          DEFAULT: withVar("--brand-500"),
          ...ramp("brand", [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]),
        },
        slate: ramp("slate", [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]),
        // Status colours follow the same rule as the brand ramp: the tint end is
        // an alert background and the dark end is its text, so both invert.
        red: ramp("red", [50, 200, 400, 600, 700, 800]),
        amber: ramp("amber", [50, 200, 400, 700, 800]),
        canvas: ramp("canvas", [50, 100, 200]),
        // The background of a card or panel. Was a literal white before dark mode.
        surface: withVar("--surface"),
        // The only legible foreground on a solid brand-green fill. It has to be
        // a token rather than a literal `text-white`, because the brand ramp is
        // tuned for white surfaces in light mode and lifted in dark mode: white
        // on the dark-mode green is 2.15:1, while near-black on it is 9.39:1.
        // So green fills carry light marks in light mode and dark marks in dark.
        "on-brand": withVar("--on-brand"),
        // The boundary of a form control, which WCAG treats as non-text content
        // needing 3:1 rather than as decoration.
        field: withVar("--field-border"),
        // Deliberately dark in both themes. Avatars, the dark CTA blocks and the
        // lightbox are dark surfaces by design, not by theme.
        ink: withVar("--ink"),
        // Non-inverting pair for chrome that sits on a photograph. A photo is a
        // photo in either theme, so its badges keep a light chip and dark text.
        paper: "#FFFFFF",
        carbon: "#1E293B",
        // Secondary marks for the same job: muted light text on an always-dark
        // block, and the brand green as it reads on a light chip. Both are
        // literal because the surfaces they sit on do not follow the theme.
        "paper-muted": "#CBD5E1",
        "brand-fixed": "#12634F",
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
        card: "0 1px 2px rgb(var(--shadow) / 0.06), 0 8px 24px -12px rgb(var(--shadow) / 0.18)",
        lift: "0 2px 4px rgb(var(--shadow) / 0.06), 0 18px 40px -18px rgb(var(--shadow) / 0.28)",
        panel: "0 24px 60px -24px rgb(var(--shadow) / 0.35)",
        // A tall, soft shadow reads as real elevation rather than a grey outline.
        float:
          "0 4px 8px -4px rgb(var(--shadow) / 0.08), 0 32px 64px -24px rgb(var(--shadow) / 0.34)",
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
          "radial-gradient(60% 60% at 12% 0%, rgb(var(--mesh) / var(--mesh-a1)) 0%, rgb(var(--mesh) / 0) 100%), radial-gradient(50% 55% at 92% 18%, rgb(var(--mesh-2) / var(--mesh-a2)) 0%, rgb(var(--mesh-2) / 0) 100%)",
        "mesh-dark":
          "radial-gradient(55% 55% at 85% 0%, rgba(27,157,128,0.32) 0%, rgba(27,157,128,0) 100%), radial-gradient(45% 60% at 8% 100%, rgba(27,157,128,0.18) 0%, rgba(27,157,128,0) 100%)",
        "grid-slate":
          "linear-gradient(to right, rgb(var(--grid) / var(--grid-a)) 1px, transparent 1px), linear-gradient(to bottom, rgb(var(--grid) / var(--grid-a)) 1px, transparent 1px)",
        "fade-up-white":
          "linear-gradient(to bottom, rgb(var(--surface) / 0) 0%, rgb(var(--surface) / 1) 100%)",
        shimmer:
          "linear-gradient(90deg, rgb(var(--slate-200) / 0) 0%, rgb(var(--slate-50) / 0.85) 50%, rgb(var(--slate-200) / 0) 100%)",
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

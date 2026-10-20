import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: { 0: "#04060D", 1: "#070B18", 2: "#0B1022" },
        ink: { DEFAULT: "#E9EDFF", muted: "#9AA3C0", dim: "#69718F" },
        accent: { DEFAULT: "#2B59FF", bright: "#4C7DFF", soft: "#5B7CFF" },
        sev: {
          critical: "#FF4D6A",
          high: "#FF8A3D",
          medium: "#F5C451",
          low: "#4CC38A",
        },
        ok: "#3DDC97",
        warn: "#F5C451",
        bad: "#FF4D6A",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: { pill: "999px", card: "20px", chip: "10px" },
      boxShadow: {
        glow: "0 0 0 1px rgba(76,125,255,.35), 0 8px 40px rgba(43,89,255,.35)",
        card: "0 1px 0 rgba(255,255,255,.04) inset, 0 20px 60px rgba(0,0,0,.45)",
      },
      letterSpacing: { display: "-0.04em", title: "-0.03em" },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(76,125,255,.55)" },
          "100%": { boxShadow: "0 0 0 10px rgba(76,125,255,0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-6px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        rise: "rise .6s cubic-bezier(.2,.7,.2,1) both",
        pulseRing: "pulseRing 1.4s ease-out infinite",
        shimmer: "shimmer 1.6s linear infinite",
        slideIn: "slideIn .25s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;

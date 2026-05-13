/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ── Design System tokens (DESIGN_SYSTEM.md §3) ── */
        bg: {
          base:     '#f7f1e8',
          elevated: '#ffffff',
          soft:     '#fdf6ea',
          warm:     '#ebe0cd',
        },
        ink: {
          strong:  '#3d2818',
          DEFAULT: '#5a3d2b',
          warm:    '#6b4a35',
          muted:   '#8a6648',
        },
        dark: {
          DEFAULT: '#4a3120',
          2:       '#5a3d2b',
          deep:    '#3d2818',
        },
        terra: {
          400: '#d97757',
          500: '#c2562e',
          700: '#8a3a1c',
        },
        blue: {
          brand: '#2d5a82',
        },
        olive: {
          DEFAULT: '#7a8c5c',
          deep:    '#5d6b46',
        },
        gold: {
          DEFAULT: '#b8893a',
          light:   '#e8b45a',
        },
        coral: '#e8a691',

        /* ── Shadcn CSS-var tokens (para @apply bg-background etc.) ── */
        background: 'hsl(var(--background, 0 0% 100%))',
        foreground: 'hsl(var(--foreground, 0 0% 3.9%))',
        border:     'hsl(var(--border, 0 0% 89.8%))',
        ring:       'hsl(var(--ring, 0 0% 63.9%))',
        input:      'hsl(var(--input, 0 0% 89.8%))',

        /* ── Legacy aliases (mantener compatibilidad) ── */
        primary: {
          50:  '#fdf6f3',
          100: '#f9ece4',
          200: '#f2d5c5',
          300: '#e8b49a',
          400: '#d97757',
          500: '#c2562e',
          600: '#b04e2b',
          700: '#8a3a1c',
          800: '#7a3520',
          900: '#5c2714',
        },
        warm: {
          50:  '#f7f1e8',
          100: '#fdf6ea',
          200: '#ebe0cd',
          300: '#d4c5bb',
          400: '#bba99c',
        },
        bark: {
          900: '#3d2818',
          800: '#5a3d2b',
          700: '#6b4a35',
          500: '#8a6648',
          400: '#a07855',
          300: '#c4a491',
          100: '#f2e6de',
        },
      },
      fontFamily: {
        sans:  ['Geist', 'system-ui', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
        mono:  ['"Geist Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        'xl':  '12px',
        '2xl': '18px',
        '3xl': '22px',
        '4xl': '28px',
      },
      boxShadow: {
        'warm-sm': '0 1px 0 rgba(61,40,24,0.04)',
        'warm':    '0 1px 0 rgba(61,40,24,0.04), 0 8px 24px -16px rgba(61,40,24,0.10)',
        'warm-lg': '0 8px 32px -12px rgba(61,40,24,0.16)',
        'terra':   '0 8px 32px -8px rgba(194,86,46,0.30)',
        'modal':   '0 50px 100px -30px rgba(0,0,0,0.40)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

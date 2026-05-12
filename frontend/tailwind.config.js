/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Paleta terracota (primary) ──
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
        // ── Fondos cálidos crema ──
        warm: {
          50:  '#f7f1e8',
          100: '#fdf6ea',
          200: '#ebe0cd',
          300: '#d4c5bb',
          400: '#bba99c',
        },
        // ── Tinta / texto ──
        bark: {
          900: '#3d2818',
          800: '#5a3d2b',
          700: '#6b4a35',
          500: '#8a6648',
          300: '#c4a491',
          100: '#f2e6de',
        },
        // ── Zonas oscuras ──
        dark: {
          DEFAULT: '#4a3120',
          2:       '#5a3d2b',
          deep:    '#3d2818',
        },
        // ── Acentos secundarios ──
        terra: {
          400: '#d97757',
          500: '#c2562e',
          700: '#8a3a1c',
        },
        drtpe: {   // azul profundo
          DEFAULT:  '#2d5a82',
          light:    '#4d6a8a',
        },
        olive: {
          DEFAULT: '#7a8c5c',
          deep:    '#5d6b46',
        },
        gold: {
          DEFAULT: '#b8893a',
          light:   '#e8b45a',
        },
        coral: {
          DEFAULT: '#e8a691',
        },
        // ── Secundario esmeralda ──
        secondary: {
          500: '#2D8B6F',
          600: '#1F6B53',
        },
      },
      fontFamily: {
        sans:  ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        serif: ['Instrument Serif', 'Georgia', 'serif'],
        mono:  ['Geist Mono', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        xl2: '1rem',
        xl3: '1.25rem',
      },
      boxShadow: {
        'warm-sm': '0 1px 3px 0 rgba(61,40,24,0.06), 0 1px 2px -1px rgba(61,40,24,0.04)',
        'warm':    '0 4px 12px 0 rgba(61,40,24,0.08), 0 2px 6px -2px rgba(61,40,24,0.05)',
        'warm-lg': '0 10px 24px 0 rgba(61,40,24,0.10), 0 4px 10px -4px rgba(61,40,24,0.06)',
        'terra':   '0 8px 32px 0 rgba(194,86,46,0.25)',
        'glow':    '0 0 40px 0 rgba(194,86,46,0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

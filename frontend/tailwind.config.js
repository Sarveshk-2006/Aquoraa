/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        /* Aquora brand palette */
        aq: {
          navy:        '#0f2340',
          'navy-hover': '#1a3354',
          'navy-active': '#1f3d65',
          blue:        '#1a56db',
          'blue-light': '#3b82f6',
          aqua:        '#0891b2',
          bg:          '#eef2f7',
          border:      'rgba(15,35,64,0.09)',
          muted:       '#5a7299',
        },
        /* Keep brand and slate for compatibility */
        brand: {
          50:  '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#082f49',
        },
        slate: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      boxShadow: {
        'aq-card': '0 1px 3px rgba(15,35,64,0.08), 0 0 0 1px rgba(15,35,64,0.05)',
        'aq-card-hover': '0 4px 12px rgba(15,35,64,0.12), 0 0 0 1px rgba(15,35,64,0.08)',
        'aq-map': '0 2px 8px rgba(15,35,64,0.12)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
      animation: {
        'fadein': 'aq-fadein 200ms ease both',
        'pulse-dot': 'aq-pulse-dot 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        main: {
          bg: '#f8fafc', // Slate-50, slight cool tint
        },
        surface: {
          DEFAULT: '#ffffff',
          hover: '#f1f5f9', // Slate-100
          active: '#e2e8f0', // Slate-200
          glass: 'rgba(255, 255, 255, 0.7)',
        },
        sidebar: {
          bg: '#0f172a', // Slate-900 - Deep, rich blue-black
          hover: '#1e293b', // Slate-800
          active: '#334155', // Slate-700
          border: '#1e293b',
        },
        border: {
          DEFAULT: '#e2e8f0', // Slate-200
          strong: '#cbd5e1', // Slate-300
          subtle: '#f1f5f9', // Slate-100
        },
        accent: {
          DEFAULT: '#002060', // Royal Blue - vivid and AI-like
          hover: '#1d4ed8',
          light: '#eff6ff', // Blue-50
          fg: '#ffffff',
          glow: 'rgba(37, 99, 235, 0.5)',
        },
        secondary: {
          DEFAULT: '#d97706', // Amber-600 - retained for legal warmth
          hover: '#b45309',
          light: '#fffbeb',
        },
        content: {
          primary: '#0f172a', // Slate-900
          secondary: '#475569', // Slate-600
          muted: '#94a3b8', // Slate-400
          inverse: '#f8fafc', // Slate-50
        },
        message: {
          user: '#002060', // Matches accent
          ai: '#ffffff', // Clean white on grey bg
          ai_bg: 'rgba(255, 255, 255, 0.8)', // Glassy
          system: '#64748b',
        },
        success: {
          DEFAULT: '#10b981',
          light: '#ecfdf5',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fffbeb',
        },
        error: {
          DEFAULT: '#ef4444',
          light: '#fef2f2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Merriweather', 'Georgia', 'serif'], // For legal text
        mono: ['JetBrains Mono', 'monospace'], // For citations/code
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        'glow': '0 0 15px rgba(37, 99, 235, 0.3)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
      },
      backdropBlur: {
        xs: '2px',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'conic-gradient(from 180deg at 50% 50%, #eff6ff 0deg, #f8fafc 180deg, #eff6ff 360deg)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
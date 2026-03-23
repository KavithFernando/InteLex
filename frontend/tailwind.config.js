export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme-sensitive: backed by CSS variables so a class swap changes them all
        main: {
          // rgb(var(--color-main-bg) / <alpha-value>) lets Tailwind opacity modifiers work
          bg: 'rgb(var(--color-main-bg) / <alpha-value>)',
        },
        surface: {
          DEFAULT: 'rgb(var(--color-surface) / <alpha-value>)',
          hover: 'rgb(var(--color-surface-hover) / <alpha-value>)',
          active: 'rgb(var(--color-surface-active) / <alpha-value>)',
          glass: 'rgb(var(--color-surface) / 0.8)',
        },
        border: {
          DEFAULT: 'rgb(var(--color-border) / <alpha-value>)',
          strong: 'rgb(var(--color-border-strong) / <alpha-value>)',
          subtle: 'rgb(var(--color-border-subtle) / <alpha-value>)',
        },
        content: {
          primary: 'rgb(var(--color-content-primary) / <alpha-value>)',
          secondary: 'rgb(var(--color-content-secondary) / <alpha-value>)',
          muted: 'rgb(var(--color-content-muted) / <alpha-value>)',
          inverse: 'rgb(var(--color-main-bg) / <alpha-value>)',
        },
        message: {
          user: '#6366f1',
          ai: 'rgb(var(--color-surface) / <alpha-value>)',
          ai_bg: 'rgb(var(--color-surface) / 0.9)',
          system: '#64748b',
        },

        // Sidebar: theme-sensitive via CSS variables
        sidebar: {
          bg: 'rgb(var(--color-sidebar-bg) / <alpha-value>)',
          hover: 'rgb(var(--color-sidebar-hover) / <alpha-value>)',
          active: 'rgb(var(--color-sidebar-active) / <alpha-value>)',
          border: 'rgb(var(--color-sidebar-border) / <alpha-value>)',
          text: 'rgb(var(--color-sidebar-text) / <alpha-value>)',
          muted: 'rgb(var(--color-sidebar-muted) / <alpha-value>)',
        },
        // Accent: theme-sensitive via CSS variables (dark = indigo, light = royal blue)
        accent: {
          DEFAULT: 'rgb(var(--color-accent) / <alpha-value>)',
          hover: 'rgb(var(--color-accent-hover) / <alpha-value>)',
          light: 'rgb(var(--color-accent) / 0.12)',
          fg: '#ffffff',
          glow: 'rgb(var(--color-accent) / 0.35)',
        },
        secondary: {
          DEFAULT: '#f59e0b',
          hover: '#fbbf24',
          light: 'rgba(245, 158, 11, 0.12)',
        },
        success: {
          DEFAULT: '#10b981',
          light: 'rgba(16, 185, 129, 0.12)',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: 'rgba(245, 158, 11, 0.12)',
        },
        error: {
          DEFAULT: '#ef4444',
          light: 'rgba(239, 68, 68, 0.12)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Merriweather', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.3)',
        'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.4)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.4)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.4)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.5), 0 8px 10px -6px rgb(0 0 0 / 0.5)',
        'glow': 'var(--shadow-glow)',
        'glow-sm': 'var(--shadow-glow-sm)',
        'glow-lg': 'var(--shadow-glow-lg)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.4)',
        'glass-light': '0 8px 32px 0 rgba(31, 38, 135, 0.08)',
      },
      backdropBlur: {
        xs: '2px',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'aurora': 'linear-gradient(135deg, rgba(59,130,246,0.15) 0%, transparent 40%, rgba(37,99,235,0.1) 70%, transparent 100%)',
        'aurora-intense': 'linear-gradient(135deg, rgba(59,130,246,0.25) 0%, rgba(37,99,235,0.15) 50%, rgba(14,165,233,0.08) 100%)',
        'indigo-gradient': 'linear-gradient(135deg, #1d4ed8, #3b82f6)',
        'user-bubble': 'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)',
      },
      animation: {
        'aurora': 'aurora 10s ease infinite',
        'ai-pulse': 'ai-pulse 2.5s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'fade-in-up': 'fade-in-up 0.4s ease-out',
        'slide-in': 'slide-in 0.3s ease-out',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        aurora: {
          '0%, 100%': { backgroundPosition: '0% 50%', opacity: '0.6' },
          '50%': { backgroundPosition: '100% 50%', opacity: '1' },
        },
        'ai-pulse': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.4)' },
          '50%': { boxShadow: '0 0 0 6px rgba(59, 130, 246, 0)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-in-up': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        main: { 
          bg: '#f6f7f6',
        },
        surface: {
          DEFAULT: '#ffffff',
          hover: '#f0f4fd',
          active: '#e0e9fc',
        },
        sidebar: { 
          bg: '#1a2e35',
        },
        border: {
          DEFAULT: '#e5e7eb',
          strong: '#9ca3af',
        },
        accent: {
          DEFAULT: '#002060',
          hover: '#003080',
          light: '#e6edf7',
          fg: '#ffffff',
        },
        secondary: {
          DEFAULT: '#d97706',
          hover: '#b45309',
          light: '#fffbeb',
        },
        content: {
          primary: '#1c1917',
          secondary: '#57534e',
          muted: '#a8a29e',
          inverse: '#f5f5f4',
        },
        message: {
          user: '#002060',
          ai: '#1a2e35',
          system: '#78716c',
        },
        link: {
          DEFAULT: '#003d99',
          hover: '#002060',
        },
        success: {
          DEFAULT: '#10b981', 
          light: '#d1fae5',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fef3c7',
        },
        error: {
          DEFAULT: '#e11d48',
          light: '#ffe4e6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'message': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
}
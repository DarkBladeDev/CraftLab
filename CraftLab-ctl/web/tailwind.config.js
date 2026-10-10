/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ctl: {
          bg: '#0b0f19',
          card: '#111827',
          surface: '#1e293b',
          border: '#334155',
          accent: '#2563eb',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
        },
        mc: {
          dark: '#121214',
          card: '#1a1a1e',
          border: '#2a2a32',
          accent: '#22c55e',
          gold: '#eab308',
          red: '#ef4444',
          blue: '#3b82f6',
        }
      }
    },
  },
  plugins: [],
}

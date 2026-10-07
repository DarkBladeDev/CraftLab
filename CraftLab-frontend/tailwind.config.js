/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
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

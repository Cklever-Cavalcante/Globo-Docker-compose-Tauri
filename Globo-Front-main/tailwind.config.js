/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        globo: {
          dark: '#121212',
          card: '#1E1E1E',
          primary: '#F47F20', // Laranja
          accent: '#00BCE4',  // Azul
          success: '#4CAF50',
          warning: '#FFC107',
          danger: '#F44336',
          text: '#E0E0E0'
        }
      }
    },
  },
  plugins: [],
}
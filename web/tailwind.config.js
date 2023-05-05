/** @type {import('tailwindcss').Config} */
// const { fontFamily } = require('tailwindcss/defaultTheme')
const forms = require('@tailwindcss/forms');

module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'media',
  plugins: [forms],
  theme: {
    extend: {
      colors: {
        brand: '#E21F58',
        'container-primary': '#FFFFFF',
        'container-secondary': '#E4E4E7',
        'container-border': '#A1A1AA',
        'surface-primary': '#3F3F46',
        'surface-secondary': '#52525B',
        'surface-tertiary': '#A1A1AA',
        'primary-accent': '#EF4444',
        'logo-gradient-start': '#F8481E',
        'logo-gradient-end': '#E01C5C',
        'brand-gradient-start': '#EC4899',
        'brand-gradient-end': '##C084FC',
      },
      fontFamily: {
        sans: ['var(--font-inter)'],
      },
    },
  },
};

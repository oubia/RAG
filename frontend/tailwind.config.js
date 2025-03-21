/** @type {import('tailwindcss').Config} */

module.exports = {
  // Specify the files Tailwind should scan for class names
  content: ['./src/**/*.{js,jsx,ts,tsx}'],

  // Customize your theme here
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        sm: '100%', 
        md: '640px',
        lg: '768px',
        xl: '1024px',
        '2xl': '1200px',
      },
    },
    extend: {
      colors: {
        primary: {
          DEFAULT: '#00a481', 
          dark: '#065f46',    
        },
        animation: {
          'pulse-red': 'pulseRed 2s infinite',
        },
      },
      keyframes: {
        fadeIn: {
          from: { opacity: 0, transform: 'translateY(-2px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        pulseRed: {
          '0%, 100%': { borderColor: '#EF4444' }, 
          '50%': { borderColor: '#F87171' }, 
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.3s ease-in-out', 
      },
    },
  },

  darkMode: 'class',

  plugins: [],
};

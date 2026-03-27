import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Nunito', 'sans-serif'],
        hand: ['"Zhi Mang Xing"', 'cursive'],
      },
      colors: {
        milk: {
          50: '#FFFEF9',
          100: '#FFF9E1',
          200: '#FFEBB6',
          300: '#FFD988',
          400: '#FFC85C',
          500: '#FFB302',
        },
        coffee: {
          50: '#FBF7F4',
          100: '#F2E8DF',
          200: '#D7CCC8',
          800: '#5D4037',
          900: '#3E2723',
        },
        accent: {
          pink: '#FFAB91',
          green: '#A5D6A7',
          blue: '#90CAF9',
        },
      },
      boxShadow: {
        soft: '0 10px 40px -10px rgba(93, 64, 55, 0.08)',
        float: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'inner-light': 'inset 0 2px 4px 0 rgba(255, 255, 255, 0.3)',
      },
      backgroundImage: {
        'stripe-pattern':
          'repeating-linear-gradient(90deg, #FFF9E1, #FFF9E1 20px, #FFFEF9 20px, #FFFEF9 40px)',
        'grid-pattern':
          'linear-gradient(#FFEBB6 2px, transparent 2px), linear-gradient(90deg, #FFEBB6 2px, transparent 2px)',
        'paper-texture': 'url("https://www.transparenttextures.com/patterns/notebook.png")',
      },
      animation: {
        'bounce-slow': 'bounce 3s infinite',
        float: 'float 4s ease-in-out infinite',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        wiggle: 'wiggle 1s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;

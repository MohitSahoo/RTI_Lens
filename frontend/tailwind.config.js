/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0B1020",
        primary: {
          DEFAULT: "#00D4FF",
          glow: "rgba(0, 212, 255, 0.4)",
        },
        secondary: {
          DEFAULT: "#7C3AED",
          glow: "rgba(124, 58, 237, 0.4)",
        },
        success: "#00FF9D",
        warning: "#FFC857",
        danger: "#FF5C8A",
        card: "rgba(17, 24, 39, 0.7)",
        "card-border": "rgba(255, 255, 255, 0.1)",
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(circle at 50% 50%, rgba(0, 212, 255, 0.15) 0%, transparent 50%)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 3s infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: 0.5, filter: 'blur(20px)' },
          '50%': { opacity: 0.8, filter: 'blur(40px)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        }
      }
    },
  },
  plugins: [],
}

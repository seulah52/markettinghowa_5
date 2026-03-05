/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{ts,tsx,js,jsx}', './components/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        red:       { DEFAULT: '#C8102E', deep: '#8B0000' },
        gold:      { DEFAULT: '#C9A84C', lt: '#F0D080' },
        ink:       '#fbfbfb',
        parchment: '#0D0D0D',
        mist:      '#E8E2D9',
      },
            fontFamily: {
        cormorant: ['"Cormorant Garamond"', 'serif'],
        noto:      ['"Noto Sans KR"', 'sans-serif'],
        notosc:    ['"Noto Serif SC"', 'serif'],
        myungjo:   ['"KimjungchulMyungjo"', 'serif'],
      },
      backgroundImage: {
        'red-glow':  'radial-gradient(ellipse at center, rgba(200,16,46,.35) 0%, transparent 70%)',
        'gold-glow': 'radial-gradient(ellipse at center, rgba(201,168,76,.25) 0%, transparent 70%)',
      },
      boxShadow: {
        'soft': '0 10px 30px rgba(31, 29, 27, 0.05)',
        'brand': '0 8px 25px rgba(184, 46, 38, 0.15)',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        marqueeRev: {
          '0%': { transform: 'translateX(-50%)' },
          '100%': { transform: 'translateX(0%)' },
        }
      },
      animation: {
        marquee: 'marquee 30s linear infinite',
        marqueeRev: 'marqueeRev 30s linear infinite',
        'spin-slow': 'spin 20s linear infinite',
      },
    },
  },
  plugins: [],
};
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        // Recall Design Tokens (与后端/设计系统一致)
        primary: {
          DEFAULT: '#5645d4',
          pressed: '#4534b3',
          deep: '#3a2a99',
        },
        ai: { start: '#6366f1', end: '#8b5cf6' },
        navy: '#0a1530',
        link: { DEFAULT: '#0075de', pressed: '#005bab' },
        ink: '#1a1a1a',
        charcoal: '#37352f',
        slate: '#5d5b54',
        steel: '#787671',
        stone: '#a4a097',
        success: '#1aae39',
        warning: '#dd5b00',
        error: '#e03131',
        info: '#0075de',
        tint: {
          lavender: '#e6e0f5', sky: '#dcecfa', mint: '#d9f3e1',
          peach: '#ffe8d4', yellow: '#fef7d6',
        },
      },
      borderRadius: {
        xs: '4px', sm: '6px', md: '8px', lg: '12px', xl: '16px', '2xl': '20px',
      },
      boxShadow: {
        xs: '0 1px 2px rgba(10,21,48,.05)',
        sm: '0 1px 3px rgba(10,21,48,.06), 0 1px 2px rgba(10,21,48,.04)',
        md: '0 4px 12px rgba(10,21,48,.08), 0 2px 4px rgba(10,21,48,.04)',
        lg: '0 12px 32px rgba(10,21,48,.10), 0 4px 8px rgba(10,21,48,.05)',
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}

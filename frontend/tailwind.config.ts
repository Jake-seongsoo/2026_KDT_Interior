import type { Config } from 'tailwindcss'

// Tailwind v4: 색상 테마는 globals.css의 @theme 블록에서 정의
const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
}

export default config

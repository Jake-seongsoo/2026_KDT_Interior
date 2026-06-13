import type { Metadata } from 'next'
import './globals.css'
import { Header } from '@/components/common/Header'

export const metadata: Metadata = {
  title: 'Moodie — 내 공간의 무드를 찾다',
  description: '도면 업로드만으로 AI가 제안하는 인테리어 톤과 방별 연출안',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang='ko'>
      <head>
        <link rel='preconnect' href='https://fonts.googleapis.com' />
        <link rel='preconnect' href='https://fonts.gstatic.com' crossOrigin='' />
        <link
          href='https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&display=swap'
          rel='stylesheet'
        />
      </head>
      <body className='min-h-screen antialiased'>
        <Header />
        <main>{children}</main>
      </body>
    </html>
  )
}

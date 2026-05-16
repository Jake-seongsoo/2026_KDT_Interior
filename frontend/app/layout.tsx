import type { Metadata } from 'next'
import './globals.css'
import { Header } from '@/components/common/Header'

export const metadata: Metadata = {
  title: 'AI 인테리어 추천',
  description: '도면 업로드만으로 AI가 제안하는 인테리어 톤과 방별 연출안',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang='ko'>
      <body className='min-h-screen antialiased'>
        <Header />
        <main>{children}</main>
      </body>
    </html>
  )
}

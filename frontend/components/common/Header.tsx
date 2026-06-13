'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { Clock, Home } from 'lucide-react'
import { useAuthUser } from '@/hooks/useAuthUser'
import { LoginButton } from './LoginButton'

export function Header() {
  const pathname = usePathname()
  const user = useAuthUser()
  const isLoginPage = pathname === '/auth/login'

  return (
    <header className='sticky top-0 z-40 border-b border-stone-200/80 bg-ivory/90 backdrop-blur'>
      <div className='mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6'>
        <Link href='/' className='flex items-center gap-2 text-stone-900'>
          <Image
            src='/moodie-mark.png'
            alt='Moodie 로고'
            width={521}
            height={403}
            priority
            className='h-8 w-auto'
          />
          <span
            className='text-lg font-semibold tracking-tight text-stone-900'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Moodie
          </span>
        </Link>
        <nav className='flex items-center gap-2 sm:gap-4'>
          <Link
            href='/'
            className='inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium text-stone-500 transition-colors hover:bg-stone-100 hover:text-stone-900'
            aria-label='홈으로 이동'
          >
            <Home size={18} strokeWidth={1.8} />
            <span className='hidden sm:inline'>홈</span>
          </Link>
          {user && (
            <Link
              href='/history'
              className='inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium text-stone-500 transition-colors hover:bg-stone-100 hover:text-stone-900'
              aria-label='분석 기록 보기'
            >
              <Clock size={18} strokeWidth={1.8} />
              <span className='hidden sm:inline'>기록</span>
            </Link>
          )}
          {!isLoginPage && <LoginButton />}
        </nav>
      </div>
    </header>
  )
}

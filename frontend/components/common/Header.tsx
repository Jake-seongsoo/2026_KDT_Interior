'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LoginButton } from './LoginButton'

export function Header() {
  const pathname = usePathname()
  const isLoginPage = pathname === '/auth/login'

  return (
    <header className='sticky top-0 z-40 border-b border-stone-200/80 bg-[#F5EFE5]/90 backdrop-blur'>
      <div className='mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6'>
        <Link href='/' className='flex items-center gap-3 text-stone-900'>
          <span
            className='flex h-8 w-8 items-center justify-center rounded-lg bg-stone-900 text-amber-100 text-sm font-bold'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            AI
          </span>
          <span
            className='text-lg font-semibold tracking-tight text-stone-900'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Interior
          </span>
        </Link>
        <nav className='flex items-center gap-2 sm:gap-4'>
          <Link
            href='/'
            className='inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium text-stone-500 transition-colors hover:bg-stone-100 hover:text-stone-900'
          >
            <span className='hidden sm:inline'>도면 분석</span>
          </Link>
          {!isLoginPage && <LoginButton />}
        </nav>
      </div>
    </header>
  )
}

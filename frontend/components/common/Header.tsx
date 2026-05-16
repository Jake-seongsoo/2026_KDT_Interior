'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Sparkles } from 'lucide-react'
import { LoginButton } from './LoginButton'

export function Header() {
  const pathname = usePathname()
  const isLoginPage = pathname === '/auth/login'

  return (
    <header className='sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur'>
      <div className='mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6'>
        <Link href='/' className='flex items-center gap-2 text-slate-950'>
          <span className='flex h-9 w-9 items-center justify-center rounded-lg bg-slate-950 text-white'>
            <Sparkles className='h-4 w-4' />
          </span>
          <span className='font-bold tracking-tight'>AI Interior</span>
        </Link>
        <nav className='flex items-center gap-2 sm:gap-4'>
          <Link
            href='/'
            className='inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-950'
          >
            <Home className='h-4 w-4' />
            <span className='hidden sm:inline'>도면 분석</span>
          </Link>
          {!isLoginPage && <LoginButton />}
        </nav>
      </div>
    </header>
  )
}

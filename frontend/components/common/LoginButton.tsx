'use client'

import { LogIn, LogOut } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { useAuthUser } from '@/hooks/useAuthUser'
import { Button } from '@/components/ui/button'

export function LoginButton() {
  const user = useAuthUser()

  const handleLogin = async () => {
    const supabase = createClient()
    const next = `${location.pathname}${location.search}`
    const redirectTo = `${location.origin}/auth/callback?next=${encodeURIComponent(next)}`

    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo },
    })
  }

  const handleLogout = async () => {
    // signOut 후 상태는 useAuthUser의 onAuthStateChange 구독이 갱신한다
    const supabase = createClient()
    await supabase.auth.signOut()
  }

  if (user) {
    return (
      <div className='flex items-center gap-2'>
        <span className='hidden max-w-32 truncate text-sm text-stone-500 sm:block'>
          {user.email?.split('@')[0]}
        </span>
        <Button onClick={handleLogout} variant='outline' size='sm'>
          <LogOut className='h-4 w-4' />
          <span className='hidden sm:inline'>로그아웃</span>
        </Button>
      </div>
    )
  }

  return (
    <Button onClick={handleLogin} variant='primary' size='sm'>
      <LogIn className='h-4 w-4' />
      로그인
    </Button>
  )
}

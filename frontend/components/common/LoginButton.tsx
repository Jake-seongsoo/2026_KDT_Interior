'use client'

import { useEffect, useState } from 'react'
import { LogIn, LogOut } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import type { User } from '@supabase/supabase-js'

export function LoginButton() {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const supabase = createClient()

    supabase.auth.getSession()
      .then(({ data }) => setUser(data.session?.user ?? null))
      .catch(() => setUser(null))

    supabase.auth.getUser()
      .then(({ data }) => {
        if (data.user) setUser(data.user)
      })
      .catch(() => setUser(null))

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })
    return () => subscription.unsubscribe()
  }, [])

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
    const supabase = createClient()
    await supabase.auth.signOut()
    setUser(null)
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

'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'

/** Supabase 로그인 사용자 상태를 구독한다. 비로그인 시 null.
 *
 * 세션 즉시 조회 + getUser 검증 + onAuthStateChange 구독을 함께 처리한다.
 * Header·LoginButton 등 로그인 여부가 필요한 컴포넌트가 공유한다.
 */
export function useAuthUser(): User | null {
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

  return user
}

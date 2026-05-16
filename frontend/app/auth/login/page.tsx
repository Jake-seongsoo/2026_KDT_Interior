'use client'

import { LogIn } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export default function LoginPage() {
  const handleGoogleLogin = async () => {
    const supabase = createClient()
    const params = new URLSearchParams(location.search)
    const next = params.get('next') ?? '/'
    const redirectTo = `${location.origin}/auth/callback?next=${encodeURIComponent(next)}`

    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo },
    })
  }

  return (
    <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-10'>
      <Card className='w-full max-w-sm'>
        <CardContent className='space-y-6 p-6 sm:p-8'>
          <div className='space-y-2 text-center'>
            <h1 className='text-2xl font-bold text-slate-950'>로그인</h1>
            <p className='text-sm leading-6 text-slate-500'>
              AI 분석과 렌더링 요청을 위해 Google 계정으로 로그인해 주세요.
            </p>
          </div>

          <Button onClick={handleGoogleLogin} variant='outline' className='w-full'>
            <LogIn className='h-4 w-4' />
            Google 계정으로 로그인
          </Button>

          <p className='text-center text-xs leading-5 text-slate-400'>
            업로드한 도면은 분석 목적으로만 사용되며 30일 후 삭제됩니다.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

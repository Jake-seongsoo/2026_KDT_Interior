'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { AuthRequiredError, getSessionHistory } from '@/lib/api'
import { ErrorScreen } from '@/components/common/ErrorScreen'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { HistorySessionCard } from '@/components/history/HistorySessionCard'
import { Button } from '@/components/ui/button'
import type { HistoryResponse } from '@/types/api'

export default function HistoryPage() {
  const router = useRouter()
  const [data, setData] = useState<HistoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    getSessionHistory()
      .then(res => {
        if (!ignore) setData(res)
      })
      .catch(e => {
        if (ignore) return
        if (e instanceof AuthRequiredError) {
          router.replace('/auth/login?next=/history')
          return
        }
        setError(e instanceof Error ? e.message : '분석 기록을 불러오지 못했습니다.')
      })

    return () => {
      ignore = true
    }
  }, [router])

  if (error) return <ErrorScreen message={error} />
  if (!data) return <LoadingScreen />

  return (
    <div className='min-h-[calc(100vh-4rem)] bg-ivory'>
      <div className='mx-auto max-w-3xl px-4 py-10 sm:px-6'>
        <div className='mb-8'>
          <p className='mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700'>
            My History
          </p>
          <h1
            className='text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            분석 기록
          </h1>
          <p className='mt-3 text-sm text-stone-500'>
            최근 분석한 도면과 생성한 시안을 다시 확인할 수 있습니다.
          </p>
        </div>

        {data.sessions.length === 0 ? (
          <div className='rounded-2xl border border-stone-200 bg-white p-10 text-center shadow-sm'>
            <p className='text-sm text-stone-500'>아직 분석한 기록이 없습니다.</p>
            <Button asChild className='mt-4'>
              <Link href='/'>새 도면 분석하기</Link>
            </Button>
          </div>
        ) : (
          <div className='space-y-4'>
            {data.sessions.map(session => (
              <HistorySessionCard key={session.session_id} session={session} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

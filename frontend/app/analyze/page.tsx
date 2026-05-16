'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { AuthRequiredError, postAnalyze } from '@/lib/api'
import { StepProgress } from '@/components/common/StepProgress'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

const STEPS = [
  '도면 업로드 중',
  'Claude Vision으로 방 구성 분석 중',
  '2026 트렌드 기반 톤 후보 생성 중',
]
const STEP_ESTIMATES_SECONDS = [3, 12, 55]

export default function AnalyzePage() {
  const router = useRouter()
  const [stepIdx, setStepIdx] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const called = useRef(false)

  useEffect(() => {
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (called.current) return
    called.current = true

    const run = async () => {
      let trendStepTimer: number | undefined
      try {
        const base64 = sessionStorage.getItem('upload:file:base64')
        const name = sessionStorage.getItem('upload:file:name') ?? 'floorplan.jpg'
        const type = sessionStorage.getItem('upload:file:type') ?? 'image/jpeg'
        const floorArea = Number(sessionStorage.getItem('upload:floorArea') ?? '30')

        if (!base64) {
          router.replace('/')
          return
        }

        setStepIdx(0)
        const res = await fetch(base64)
        const blob = await res.blob()
        const file = new File([blob], name, { type })

        setStepIdx(1)
        trendStepTimer = window.setTimeout(() => setStepIdx(2), STEP_ESTIMATES_SECONDS[1] * 1000)
        const result = await postAnalyze(file, floorArea)

        sessionStorage.setItem(`analyze:${result.session_id}`, JSON.stringify(result))

        sessionStorage.removeItem('upload:file:base64')
        sessionStorage.removeItem('upload:file:name')
        sessionStorage.removeItem('upload:file:type')
        sessionStorage.removeItem('upload:floorArea')

        // 로딩바 100% 완료 상태를 잠깐 보여준 후 이동
        setStepIdx(STEPS.length)
        await new Promise((resolve) => setTimeout(resolve, 600))
        router.push(`/tones/${result.session_id}`)
      } catch (e) {
        if (e instanceof AuthRequiredError) {
          router.replace('/auth/login?next=/')
          return
        }
        setError(e instanceof Error ? e.message : '오류가 발생했습니다.')
      } finally {
        if (trendStepTimer !== undefined) window.clearTimeout(trendStepTimer)
      }
    }

    run()
  }, [router])

  const steps = STEPS.map((label, i) => ({
    label,
    done: i < stepIdx,
    active: i === stepIdx,
  }))

  return (
    <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-10'>
      <Card className='w-full max-w-md'>
        <CardContent className='space-y-8 p-6 sm:p-8'>
          <div className='space-y-2 text-center'>
            <p className='text-xs font-semibold uppercase tracking-[0.18em] text-teal-600'>Analyzing</p>
            <h1 className='text-2xl font-bold text-slate-950'>도면을 분석하고 있습니다</h1>
            <p className='text-sm text-slate-500'>보통 10~15초 정도 소요됩니다.</p>
          </div>

          {error ? (
            <div className='space-y-4'>
              <p className='rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-700'>{error}</p>
              <Button asChild className='w-full'>
                <Link href='/'>다시 시도</Link>
              </Button>
            </div>
          ) : (
            <StepProgress steps={steps} estimatedSeconds={STEP_ESTIMATES_SECONDS} elapsedSeconds={elapsed} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, postRender } from '@/lib/api'
import { StepProgress } from '@/components/common/StepProgress'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import type { ToneCandidateOut } from '@/types/api'

const STEPS = [
  '2D 배치도 생성 중',
  'Imagen으로 방별 이미지 생성 중',
  '추천 상품 검색 중',
]
const STEP_ESTIMATES_SECONDS = [3, 35, 10]

export default function RenderPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
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
      const toneRaw = sessionStorage.getItem(`tone:${sessionId}`)
      if (!toneRaw) {
        router.replace('/')
        return
      }
      const tone: ToneCandidateOut = JSON.parse(toneRaw)

      let imagenStepTimer: number | undefined
      let productsStepTimer: number | undefined
      try {
        setStepIdx(0)
        imagenStepTimer = window.setTimeout(() => setStepIdx(1), 800)
        productsStepTimer = window.setTimeout(
          () => setStepIdx(2),
          (STEP_ESTIMATES_SECONDS[0] + STEP_ESTIMATES_SECONDS[1]) * 1000,
        )

        const result = await postRender({
          session_id: sessionId,
          selected_tone_id: tone.id,
        })

        setStepIdx(2)
        sessionStorage.setItem(`render:${result.result_id}`, JSON.stringify(result))
        sessionStorage.setItem(`render_session:${result.result_id}`, sessionId)
        sessionStorage.removeItem(`tone:${sessionId}`)

        router.push(`/result/${result.result_id}`)
      } catch (e) {
        if (e instanceof AuthRequiredError) {
          router.replace(`/auth/login?next=/tones/${sessionId}`)
          return
        }
        setError(e instanceof Error ? e.message : '오류가 발생했습니다.')
      } finally {
        if (imagenStepTimer !== undefined) window.clearTimeout(imagenStepTimer)
        if (productsStepTimer !== undefined) window.clearTimeout(productsStepTimer)
      }
    }

    run()
  }, [sessionId, router])

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
            <p className='text-xs font-semibold uppercase tracking-[0.18em] text-teal-600'>Rendering</p>
            <h1 className='text-2xl font-bold text-slate-950'>방별 제안을 생성하고 있습니다</h1>
            <p className='text-sm text-slate-500'>보통 20~40초 정도 소요됩니다.</p>
          </div>

          {error ? (
            <div className='space-y-4'>
              <p className='rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-700'>{error}</p>
              <Button asChild className='w-full'>
                <Link href={`/tones/${sessionId}`}>톤 선택으로 돌아가기</Link>
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

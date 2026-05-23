'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, postRender } from '@/lib/api'
import { refinementStorage } from '@/lib/session-storage'
import { useStepFlow } from '@/hooks/useStepFlow'
import { StepProgress } from '@/components/common/StepProgress'
import { Button } from '@/components/ui/button'
import type { ToneCandidateOut } from '@/types/api'

const STEPS = [
  '2D 배치도 생성 중',
  'Imagen으로 방별 이미지 생성 중',
  '추천 상품 검색 중',
]
const STEP_ESTIMATES_SECONDS = [3, 35, 10]
const totalEstimatedSeconds = STEP_ESTIMATES_SECONDS.reduce((a, b) => a + b, 0)

function formatEstimatedTime(seconds: number): string {
  if (seconds < 60) return `약 ${seconds}초`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return secs === 0 ? `약 ${mins}분` : `약 ${mins}분 ${secs}초`
}

export default function RenderPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [toneName, setToneName] = useState<string | null>(null)
  const called = useRef(false)

  const { stepIdx, setStepIdx, elapsed, steps, complete } = useStepFlow(STEPS)

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
      setToneName(tone.name)

      let imagenStepTimer: number | undefined
      let productsStepTimer: number | undefined
      try {
        setStepIdx(0)
        imagenStepTimer = window.setTimeout(() => setStepIdx(1), 800)
        productsStepTimer = window.setTimeout(
          () => setStepIdx(2),
          (STEP_ESTIMATES_SECONDS[0] + STEP_ESTIMATES_SECONDS[1]) * 1000,
        )

        const refinement = refinementStorage.load(sessionId)
        const result = await postRender({
          session_id: sessionId,
          selected_tone_id: tone.id,
          ...(refinement ?? {}),
        })
        refinementStorage.clear(sessionId)

        sessionStorage.setItem(`render:${result.result_id}`, JSON.stringify(result))
        sessionStorage.setItem(`render_session:${result.result_id}`, sessionId)
        sessionStorage.removeItem(`tone:${sessionId}`)

        await complete(() => router.push(`/result/${result.result_id}`))
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

  return (
    <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center bg-stone-950 px-4 py-10'>
      <div className='w-full max-w-md'>
        {/* 헤더 */}
        <div className='mb-10 text-center'>
          <div className='mb-4 flex justify-center gap-1.5'>
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className='h-1.5 w-1.5 rounded-full bg-amber-500'
                style={{
                  animationName: 'pulse',
                  animationDuration: '1.5s',
                  animationDelay: `${i * 0.2}s`,
                  animationIterationCount: 'infinite',
                  animationTimingFunction: 'ease-in-out',
                  opacity: 0.6,
                }}
              />
            ))}
          </div>
          <p className='mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-600'>
            Rendering
          </p>
          <h1
            className='text-3xl font-bold text-stone-100'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            방별 제안을 생성하고 있습니다
          </h1>
          {toneName && (
            <p className='mt-3 text-sm text-stone-400'>
              <span className='text-stone-300'>"{toneName}"</span> 톤으로 렌더링 중
            </p>
          )}
          <p className='mt-1 text-sm text-stone-500'>{formatEstimatedTime(totalEstimatedSeconds)} 정도 소요됩니다.</p>
        </div>

        {error ? (
          <div className='space-y-4'>
            <p className='rounded-xl border border-red-900/30 bg-red-950/40 p-4 text-sm text-red-300'>
              {error}
            </p>
            <Button asChild className='w-full bg-stone-700 text-white hover:bg-stone-600'>
              <Link href={`/tones/${sessionId}`}>톤 선택으로 돌아가기</Link>
            </Button>
          </div>
        ) : (
          <StepProgress
            steps={steps}
            estimatedSeconds={STEP_ESTIMATES_SECONDS}
            elapsedSeconds={elapsed}
            dark
          />
        )}
      </div>
    </div>
  )
}

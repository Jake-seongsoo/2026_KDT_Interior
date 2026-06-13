'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, postRender } from '@/lib/api'
import { formatEstimatedTime } from '@/lib/format'
import { refinementStorage, renderStorage, toneStorage } from '@/lib/session-storage'
import { useStepFlow } from '@/hooks/useStepFlow'
import { LoadingDots } from '@/components/common/LoadingDots'
import { ProgressErrorBox } from '@/components/common/ProgressErrorBox'
import { StepProgress } from '@/components/common/StepProgress'
import type { ToneCandidateOut } from '@/types/api'

const STEPS = [
  '2D 배치도 생성 중',
  'Imagen으로 방별 이미지 생성 중',
  '추천 상품 검색 중',
]
const STEP_ESTIMATES_SECONDS = [3, 35, 10]
const totalEstimatedSeconds = STEP_ESTIMATES_SECONDS.reduce((a, b) => a + b, 0)

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
      const tone = toneStorage.load(sessionId)
      if (!tone) {
        router.replace('/')
        return
      }
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

        renderStorage.save(result.result_id, sessionId, result)
        toneStorage.clear(sessionId)

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
          <LoadingDots />
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
          <ProgressErrorBox
            message={error}
            actionHref={`/tones/${sessionId}`}
            actionLabel='톤 선택으로 돌아가기'
          />
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

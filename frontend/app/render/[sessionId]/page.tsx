'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, postRender } from '@/lib/api'
import { refinementStorage, renderStorage, toneStorage } from '@/lib/session-storage'
import { useStepFlow } from '@/hooks/useStepFlow'
import { ProgressPageLayout } from '@/components/common/ProgressPageLayout'
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
    <ProgressPageLayout
      label='Rendering'
      title='방별 제안을 생성하고 있습니다'
      subtitle={toneName && (
        <p className='mt-3 text-sm text-stone-400'>
          <span className='text-stone-300'>"{toneName}"</span> 톤으로 렌더링 중
        </p>
      )}
      totalEstimatedSeconds={totalEstimatedSeconds}
      error={error}
      errorActionHref={`/tones/${sessionId}`}
      errorActionLabel='톤 선택으로 돌아가기'
      steps={steps}
      estimatedSeconds={STEP_ESTIMATES_SECONDS}
      elapsedSeconds={elapsed}
    />
  )
}

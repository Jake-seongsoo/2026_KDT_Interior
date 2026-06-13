'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { AuthRequiredError, postAnalyze, postAnalyzeCustom } from '@/lib/api'
import { analyzeStorage, modeStorage, customInputStorage, referenceStorage, uploadStorage } from '@/lib/session-storage'
import { useStepFlow } from '@/hooks/useStepFlow'
import { ProgressPageLayout } from '@/components/common/ProgressPageLayout'

const AUTO_STEPS = [
  '도면 업로드 중',
  'Claude Vision으로 방 구성 분석 중',
  '2026 트렌드 기반 톤 후보 생성 중',
]

const CUSTOM_STEPS = [
  '도면 업로드 중',
  'Claude Vision으로 방 구성 분석 중',
  '입력하신 분위기로 톤 변형 생성 중',
]
const STEP_ESTIMATES_SECONDS = [3, 12, 55]

const totalEstimatedSeconds = STEP_ESTIMATES_SECONDS.reduce((a, b) => a + b, 0)

export default function AnalyzePage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [isCustomMode, setIsCustomMode] = useState(false)
  const called = useRef(false)

  const STEPS = isCustomMode ? CUSTOM_STEPS : AUTO_STEPS
  const { stepIdx, setStepIdx, elapsed, steps, complete } = useStepFlow(STEPS)

  useEffect(() => {
    if (called.current) return
    called.current = true

    const run = async () => {
      let trendStepTimer: number | undefined
      try {
        const { base64, name, type, floorArea } = uploadStorage.load()
        const mode = modeStorage.get()
        const customData = mode === 'custom' ? customInputStorage.get() : null
        const refData = referenceStorage.load()

        if (!base64) {
          router.replace('/')
          return
        }

        setIsCustomMode(mode === 'custom')
        setStepIdx(0)

        const [blob, refBlob] = await Promise.all([
          fetch(base64).then(r => r.blob()),
          refData ? fetch(refData.base64).then(r => r.blob()) : Promise.resolve(null),
        ])
        const file = new File([blob], name, { type })
        const referenceFile = refBlob && refData
          ? new File([refBlob], refData.name, { type: refData.type })
          : undefined

        setStepIdx(1)
        trendStepTimer = window.setTimeout(() => setStepIdx(2), STEP_ESTIMATES_SECONDS[1] * 1000)

        let result
        if (mode === 'custom' && customData) {
          result = await postAnalyzeCustom(file, floorArea, customData.userText, customData.moodChips, referenceFile)
        } else {
          result = await postAnalyze(file, floorArea, referenceFile)
        }

        analyzeStorage.save(result.session_id, result)

        uploadStorage.clear()
        modeStorage.clear()
        customInputStorage.clear()
        referenceStorage.clear()

        await complete(() => router.push(`/tones/${result.session_id}`))
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

  return (
    <ProgressPageLayout
      label='Analyzing'
      title='도면을 분석하고 있습니다'
      totalEstimatedSeconds={totalEstimatedSeconds}
      error={error}
      errorActionHref='/'
      errorActionLabel='다시 시도'
      steps={steps}
      estimatedSeconds={STEP_ESTIMATES_SECONDS}
      elapsedSeconds={elapsed}
    />
  )
}

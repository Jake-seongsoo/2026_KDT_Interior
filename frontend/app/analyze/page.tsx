'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { AuthRequiredError, postAnalyze, postAnalyzeCustom } from '@/lib/api'
import { modeStorage, customInputStorage } from '@/lib/session-storage'
import { StepProgress } from '@/components/common/StepProgress'
import { Button } from '@/components/ui/button'

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

function formatEstimatedTime(seconds: number): string {
  if (seconds < 60) return `약 ${seconds}초`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return secs === 0 ? `약 ${mins}분` : `약 ${mins}분 ${secs}초`
}

export default function AnalyzePage() {
  const router = useRouter()
  const [stepIdx, setStepIdx] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [isCustomMode, setIsCustomMode] = useState(false)
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
        const mode = modeStorage.get()
        const customData = mode === 'custom' ? customInputStorage.get() : null

        if (!base64) {
          router.replace('/')
          return
        }

        setIsCustomMode(mode === 'custom')
        setStepIdx(0)
        const res = await fetch(base64)
        const blob = await res.blob()
        const file = new File([blob], name, { type })

        setStepIdx(1)
        trendStepTimer = window.setTimeout(() => setStepIdx(2), STEP_ESTIMATES_SECONDS[1] * 1000)

        let result
        if (mode === 'custom' && customData) {
          result = await postAnalyzeCustom(file, floorArea, customData.userText, customData.moodChips)
        } else {
          result = await postAnalyze(file, floorArea)
        }

        sessionStorage.setItem(`analyze:${result.session_id}`, JSON.stringify(result))

        sessionStorage.removeItem('upload:file:base64')
        sessionStorage.removeItem('upload:file:name')
        sessionStorage.removeItem('upload:file:type')
        sessionStorage.removeItem('upload:floorArea')
        modeStorage.clear()
        customInputStorage.clear()

        setStepIdx((mode === 'custom' ? CUSTOM_STEPS : AUTO_STEPS).length)
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

  const STEPS = isCustomMode ? CUSTOM_STEPS : AUTO_STEPS
  const steps = STEPS.map((label, i) => ({
    label,
    done: i < stepIdx,
    active: i === stepIdx,
  }))

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
            Analyzing
          </p>
          <h1
            className='text-3xl font-bold text-stone-100'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            도면을 분석하고 있습니다
          </h1>
          <p className='mt-3 text-sm text-stone-500'>{formatEstimatedTime(totalEstimatedSeconds)} 정도 소요됩니다.</p>
        </div>

        {error ? (
          <div className='space-y-4'>
            <p className='rounded-xl border border-red-900/30 bg-red-950/40 p-4 text-sm text-red-300'>
              {error}
            </p>
            <Button asChild className='w-full bg-stone-700 text-white hover:bg-stone-600'>
              <Link href='/'>다시 시도</Link>
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

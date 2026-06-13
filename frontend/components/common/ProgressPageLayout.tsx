import { ReactNode } from 'react'
import { formatEstimatedTime } from '@/lib/format'
import { LoadingDots } from '@/components/common/LoadingDots'
import { ProgressErrorBox } from '@/components/common/ProgressErrorBox'
import { StepProgress, type Step } from '@/components/common/StepProgress'

interface ProgressPageLayoutProps {
  label: string                 // 상단 소문자 라벨 (Analyzing / Rendering)
  title: string                 // 본문 제목
  subtitle?: ReactNode          // 제목 아래 보조 줄 (선택 — 예: 선택 톤 이름)
  totalEstimatedSeconds: number
  error: string | null
  errorActionHref: string
  errorActionLabel: string
  steps: Step[]
  estimatedSeconds: number[]
  elapsedSeconds: number
}

/** 분석·렌더링 대기 페이지 공통 레이아웃 (다크 배경 + 진행 표시) */
export function ProgressPageLayout({
  label,
  title,
  subtitle,
  totalEstimatedSeconds,
  error,
  errorActionHref,
  errorActionLabel,
  steps,
  estimatedSeconds,
  elapsedSeconds,
}: ProgressPageLayoutProps) {
  return (
    <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center bg-stone-950 px-4 py-10'>
      <div className='w-full max-w-md'>
        <div className='mb-10 text-center'>
          <LoadingDots />
          <p className='mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-600'>
            {label}
          </p>
          <h1
            className='text-3xl font-bold text-stone-100'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            {title}
          </h1>
          {subtitle}
          <p className={`${subtitle ? 'mt-1' : 'mt-3'} text-sm text-stone-500`}>
            {formatEstimatedTime(totalEstimatedSeconds)} 정도 소요됩니다.
          </p>
        </div>

        {error ? (
          <ProgressErrorBox message={error} actionHref={errorActionHref} actionLabel={errorActionLabel} />
        ) : (
          <StepProgress steps={steps} estimatedSeconds={estimatedSeconds} elapsedSeconds={elapsedSeconds} dark />
        )}
      </div>
    </div>
  )
}

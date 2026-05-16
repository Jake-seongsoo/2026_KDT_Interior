'use client'

import { Check, Loader2 } from 'lucide-react'

interface Step {
  label: string
  done: boolean
  active: boolean
}

interface StepProgressProps {
  steps: Step[]
  estimatedSeconds?: number | number[]
  elapsedSeconds?: number
}

export function StepProgress({ steps, estimatedSeconds, elapsedSeconds }: StepProgressProps) {
  const estimates = Array.isArray(estimatedSeconds) ? estimatedSeconds : null
  const totalEstimate: number | undefined = estimates
    ? estimates.reduce((sum, seconds) => sum + seconds, 0)
    : typeof estimatedSeconds === 'number'
      ? estimatedSeconds
      : undefined
  const activeStepIndex = steps.findIndex((step) => step.active)
  const completedEstimate = estimates
    ? estimates.slice(0, Math.max(activeStepIndex, 0)).reduce((sum, seconds) => sum + seconds, 0)
    : 0
  const activeElapsed: number | undefined = elapsedSeconds !== undefined && estimates
    ? Math.max(0, elapsedSeconds - completedEstimate)
    : elapsedSeconds
  const activeEstimate: number | undefined = estimates && activeStepIndex >= 0 ? estimates[activeStepIndex] : totalEstimate
  const visualElapsed: number | undefined = estimates
    ? completedEstimate + Math.min(activeElapsed ?? 0, (activeEstimate ?? 0) * 0.9)
    : elapsedSeconds
  const allDone = steps.length > 0 && steps.every((step) => step.done)
  const progress = allDone
    ? 100
    : totalEstimate && visualElapsed !== undefined
      ? Math.min((visualElapsed / totalEstimate) * 100, 95)
      : null
  const remainingSeconds = allDone
    ? 0
    : totalEstimate && elapsedSeconds !== undefined
      ? Math.max(0, Math.ceil(totalEstimate - elapsedSeconds))
      : null

  return (
    <div className='space-y-6'>
      <div className='space-y-3'>
        {steps.map((step, i) => (
          <div key={i} className='flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 px-3 py-3'>
            <div
              className={[
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold',
                step.done
                  ? 'bg-teal-600 text-white'
                  : step.active
                    ? 'bg-slate-950 text-white'
                    : 'bg-white text-slate-400 ring-1 ring-slate-200',
              ].join(' ')}
            >
              {step.done ? (
                <Check className='h-4 w-4' />
              ) : step.active ? (
                <Loader2 className='h-4 w-4 animate-spin' />
              ) : (
                i + 1
              )}
            </div>
            <span
              className={[
                'text-sm',
                step.active ? 'font-semibold text-slate-950' : 'text-slate-500',
                step.done ? 'text-slate-400' : '',
              ].join(' ')}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>

      {progress !== null && (
        <div className='space-y-2'>
          <div className='h-2 overflow-hidden rounded-full bg-slate-200'>
            <div
              className='h-full rounded-full bg-teal-500 transition-all duration-1000'
              style={{ width: `${progress}%` }}
            />
          </div>
          {remainingSeconds !== null && (
            <p className='text-right text-xs text-slate-500'>
              예상 완료까지 약 {remainingSeconds}초
            </p>
          )}
        </div>
      )}
    </div>
  )
}

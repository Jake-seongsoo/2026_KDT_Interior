'use client'

import { Check } from 'lucide-react'

interface Step {
  label: string
  done: boolean
  active: boolean
}

interface StepProgressProps {
  steps: Step[]
  estimatedSeconds?: number | number[]
  elapsedSeconds?: number
  dark?: boolean
}

export function StepProgress({ steps, estimatedSeconds, elapsedSeconds, dark }: StepProgressProps) {
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

  const mutedText = dark ? 'text-stone-400' : 'text-stone-400'
  const activeText = dark ? 'text-stone-100' : 'text-stone-900'
  const doneText = dark ? 'text-stone-500' : 'text-stone-400'
  const borderColor = dark ? 'border-stone-700' : 'border-stone-200'
  const trackBg = dark ? 'bg-stone-700' : 'bg-stone-200'

  return (
    <div className='space-y-5'>
      <div className='space-y-2'>
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${borderColor} ${
              step.active
                ? dark ? 'bg-stone-800/60' : 'bg-amber-50/60'
                : dark ? 'bg-transparent' : 'bg-transparent'
            }`}
          >
            <div
              className={[
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all',
                step.done
                  ? 'bg-amber-600 text-white'
                  : step.active
                    ? dark ? 'bg-stone-100 text-stone-900' : 'bg-stone-900 text-white'
                    : dark ? 'bg-stone-700 text-stone-500' : 'bg-stone-100 text-stone-400',
              ].join(' ')}
            >
              {step.done ? (
                <Check className='h-3.5 w-3.5' />
              ) : step.active ? (
                <span className='relative flex h-2.5 w-2.5'>
                  <span className='absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60' />
                  <span className='relative inline-flex h-2.5 w-2.5 rounded-full bg-current' />
                </span>
              ) : (
                i + 1
              )}
            </div>
            <span
              className={`text-sm ${
                step.active ? activeText : step.done ? doneText : mutedText
              } ${step.active ? 'font-medium' : ''}`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>

      {progress !== null && (
        <div className='space-y-2'>
          <div className={`h-0.5 overflow-hidden rounded-full ${trackBg}`}>
            <div
              className='h-full rounded-full bg-amber-600 transition-all duration-1000'
              style={{ width: `${progress}%` }}
            />
          </div>
          {remainingSeconds !== null && (
            <p className={`text-right text-xs ${mutedText}`}>
              예상 {remainingSeconds}초 남음
            </p>
          )}
        </div>
      )}
    </div>
  )
}

'use client'

import { useCallback, useEffect, useState } from 'react'

interface StepItem {
  label: string
  done: boolean
  active: boolean
}

/**
 * 단계별 진행 UI 공통 훅 (분석·렌더링 대기 페이지 공용)
 *
 * - elapsed 타이머 (1초 간격)
 * - steps 계산 (done/active)
 * - complete(): 진행바 100% → 600ms 대기 → navigate 호출
 */
export function useStepFlow(stepLabels: string[]) {
  const [stepIdx, setStepIdx] = useState(0)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  const steps: StepItem[] = stepLabels.map((label, i) => ({
    label,
    done: i < stepIdx,
    active: i === stepIdx,
  }))

  const complete = useCallback(
    async (navigate: () => void) => {
      setStepIdx(stepLabels.length)
      await new Promise<void>((resolve) => setTimeout(resolve, 600))
      navigate()
    },
    // stepLabels.length가 바뀔 때만 재생성 (두 페이지 모두 길이 3으로 고정)
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [stepLabels.length],
  )

  return { stepIdx, setStepIdx, elapsed, steps, complete }
}

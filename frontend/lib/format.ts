/** 초 단위 예상 시간을 한국어 표기로 변환한다. (75 → '약 1분 15초') */
export function formatEstimatedTime(seconds: number): string {
  if (seconds < 60) return `약 ${seconds}초`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return secs === 0 ? `약 ${mins}분` : `약 ${mins}분 ${secs}초`
}

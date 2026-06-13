/** 초 단위 예상 시간을 한국어 표기로 변환한다. (75 → '약 1분 15초') */
export function formatEstimatedTime(seconds: number): string {
  if (seconds < 60) return `약 ${seconds}초`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return secs === 0 ? `약 ${mins}분` : `약 ${mins}분 ${secs}초`
}

/** ISO8601 문자열을 'YYYY.MM.DD' 표기로 변환한다. 파싱 실패 시 빈 문자열. */
export function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}.${m}.${day}`
}

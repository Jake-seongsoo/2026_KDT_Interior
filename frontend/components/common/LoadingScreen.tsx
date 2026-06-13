/** 전체 화면 로딩 표시 — 결과/톤 페이지 데이터 로드 중 */
export function LoadingScreen() {
  return (
    <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center bg-ivory'>
      <p className='text-sm text-stone-400'>불러오는 중...</p>
    </div>
  )
}

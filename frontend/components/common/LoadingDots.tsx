/** 진행 대기 페이지 상단의 점 3개 펄스 애니메이션 */
export function LoadingDots() {
  return (
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
  )
}

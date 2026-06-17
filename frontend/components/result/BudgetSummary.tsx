import { Wallet } from 'lucide-react'
import type { RoomResultOut } from '@/types/api'

interface BudgetSummaryProps {
  rooms: RoomResultOut[]
  /** 정밀화에서 입력한 예산(만원 단위). 없으면 합계만 표시. */
  budget10kWon?: number | null
}

function formatWon(won: number): string {
  return `${won.toLocaleString('ko-KR')}원`
}

/**
 * 추천 상품 가격 합계와 입력 예산 대비 신호를 보여준다.
 * ⚠️ 가구·소품 합계일 뿐 시공·공사비는 포함하지 않는다(법적 면책).
 */
export function BudgetSummary({ rooms, budget10kWon }: BudgetSummaryProps) {
  const products = rooms.flatMap((r) => r.products)
  if (products.length === 0) return null

  const totalMin = products.reduce((sum, p) => sum + p.price_min, 0)
  const totalMax = products.reduce((sum, p) => sum + Math.max(p.price_max, p.price_min), 0)
  const budgetWon = budget10kWon ? budget10kWon * 10_000 : null
  // 예산 대비 비율은 하한가(totalMin) 기준 — 보수적으로 표시
  const pct = budgetWon && budgetWon > 0 ? Math.round((totalMin / budgetWon) * 100) : null

  return (
    <section
      data-testid='budget-summary'
      className='no-print rounded-2xl border border-stone-200 bg-white p-5 shadow-sm'
    >
      <div className='flex items-center gap-2'>
        <Wallet className='h-4 w-4 text-amber-600' />
        <h2 className='text-sm font-semibold text-stone-900'>추천 상품 합계</h2>
        <span className='text-xs text-stone-400'>{products.length}개</span>
      </div>

      <p className='mt-3 text-2xl font-bold tracking-tight text-stone-900'>
        {formatWon(totalMin)}
        {totalMax > totalMin && (
          <span className='text-base font-normal text-stone-400'> ~ {formatWon(totalMax)}</span>
        )}
      </p>

      {budgetWon && (
        <div className='mt-4 space-y-2'>
          <div className='flex items-center justify-between text-xs text-stone-500'>
            <span>입력 예산 {budget10kWon!.toLocaleString()}만원 대비</span>
            {pct !== null && (
              <span className='font-semibold text-amber-700'>약 {pct}%</span>
            )}
          </div>
          {pct !== null && (
            <div className='h-2 overflow-hidden rounded-full bg-stone-100'>
              <div
                className='h-full rounded-full bg-amber-500 transition-all'
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
          )}
        </div>
      )}

      <p className='mt-4 border-t border-stone-100 pt-3 text-xs leading-5 text-stone-400'>
        추천 상품(가구·소품) 가격 합계이며 <span className='font-medium text-stone-500'>시공·공사비는 포함하지 않습니다</span>. 가격은 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다.
      </p>
    </section>
  )
}

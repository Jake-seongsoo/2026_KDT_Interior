import Link from 'next/link'
import { ImageIcon } from 'lucide-react'
import { formatDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { HistorySessionItem } from '@/types/api'

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  analyzing: { label: '분석 중', cls: 'bg-amber-100 text-amber-800' },
  completed: { label: '완료', cls: 'bg-emerald-100 text-emerald-800' },
  failed: { label: '실패', cls: 'bg-red-100 text-red-700' },
}

interface HistorySessionCardProps {
  session: HistorySessionItem
}

/** 분석 기록 한 건 — 도면 썸네일·요약 + 그 세션의 렌더 결과 칩 중첩. */
export function HistorySessionCard({ session }: HistorySessionCardProps) {
  const badge = STATUS_BADGE[session.status] ?? STATUS_BADGE.completed
  const isFailed = session.status === 'failed'

  return (
    <div className='overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm'>
      <div className='flex gap-4 p-4'>
        {/* 도면 썸네일 */}
        <div className='h-20 w-20 shrink-0 overflow-hidden rounded-lg border border-stone-100 bg-stone-50'>
          {session.thumbnail_url ? (
            // 도면 Signed URL(만료·쿼리스트링)이라 next/image 대신 img 사용
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={session.thumbnail_url}
              alt='도면 썸네일'
              className='h-full w-full object-cover'
            />
          ) : (
            <div className='flex h-full w-full items-center justify-center text-stone-300'>
              <ImageIcon className='h-6 w-6' />
            </div>
          )}
        </div>

        {/* 요약 정보 */}
        <div className='min-w-0 flex-1'>
          <div className='flex items-center gap-2'>
            <span className={cn('rounded-full px-2 py-0.5 text-xs font-semibold', badge.cls)}>
              {badge.label}
            </span>
            <span className='text-xs text-stone-400'>{formatDate(session.created_at)}</span>
          </div>
          <p className='mt-1.5 truncate text-sm font-medium text-stone-800'>
            {session.room_summary}
          </p>
          <p className='text-xs text-stone-400'>공급면적 {session.floor_area_pyeong}평</p>

          {/* 세션 재진입 — 실패 세션은 비활성 */}
          {isFailed ? (
            <p className='mt-2 text-xs text-red-500'>분석에 실패한 기록입니다.</p>
          ) : (
            <Link
              href={`/tones/${session.session_id}`}
              className='mt-2 inline-block text-xs font-medium text-amber-700 hover:text-amber-800 hover:underline'
            >
              톤 다시 선택하기 →
            </Link>
          )}
        </div>
      </div>

      {/* 렌더 결과 칩 (중첩) */}
      {session.results.length > 0 && (
        <div className='border-t border-stone-100 bg-stone-50/60 px-4 py-3'>
          <p className='mb-2 text-xs font-semibold uppercase tracking-wider text-stone-400'>
            생성한 시안 {session.results.length}개
          </p>
          <div className='flex flex-wrap gap-2'>
            {session.results.map(r => (
              <Link
                key={r.result_id}
                href={`/result/${r.result_id}`}
                className='inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1 text-xs font-medium text-stone-700 transition-colors hover:border-amber-400 hover:bg-amber-50'
              >
                {r.tone_name || '시안'}
                <span className='text-stone-400'>{formatDate(r.created_at)}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

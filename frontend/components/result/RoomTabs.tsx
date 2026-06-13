'use client'

import type { RoomResultOut, ToneCandidateOut } from '@/types/api'
import { RoomRenderCard } from './RoomRenderCard'

interface RoomTabsProps {
  rooms: RoomResultOut[]
  activeRoomId?: string | null
  onChange?: (roomId: string) => void
  /** 방 유형 → 배치 가전명 목록. 정밀화 시 선택된 가전이 있을 때만 전달. */
  appliancesMap?: Record<string, string[]>
  showProducts?: boolean  // 공유 페이지는 상품 제외 (false)
  /** 선택된 톤. 전달 시 PDF 첫 방 위에 톤 요약(이름+팔레트)을 표시. */
  tone?: ToneCandidateOut
}

export function RoomTabs({ rooms, activeRoomId, onChange, appliancesMap, showProducts = true, tone }: RoomTabsProps) {
  const activeIdx = activeRoomId
    ? rooms.findIndex(r => r.room_id === activeRoomId)
    : 0
  const resolvedIdx = activeIdx >= 0 ? activeIdx : 0
  const activeRoom = rooms[resolvedIdx]
  const activeAppliances = activeRoom ? (appliancesMap?.[activeRoom.room_type] ?? []) : []

  return (
    <div className='space-y-6'>
      {/* 화면용: 탭으로 선택된 방 하나만 표시 (인쇄 시 숨김) */}
      <div className='space-y-6 print:hidden'>
        {/* 탭 내비게이션 */}
        <div className='flex gap-0 overflow-x-auto border-b border-stone-200'>
          {rooms.map((room, i) => {
            const isActive = i === resolvedIdx
            return (
              <button
                key={room.room_id}
                onClick={() => onChange?.(room.room_id)}
                className={[
                  'shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'border-stone-900 text-stone-900'
                    : 'border-transparent text-stone-400 hover:border-stone-300 hover:text-stone-700',
                ].join(' ')}
              >
                {room.room_type}
              </button>
            )
          })}
        </div>

        {/* 이 방에 배치된 가전 라벨 */}
        {activeAppliances.length > 0 && (
          <div className='rounded-lg border border-amber-700/30 bg-amber-900/10 px-4 py-2.5'>
            <p className='text-xs text-stone-400'>
              <span className='font-semibold text-amber-400'>예상 배치 가전: </span>
              {activeAppliances.join(' · ')}
            </p>
            <p className='mt-0.5 text-[10px] text-stone-500'>
              AI 렌더링 예시이며 실제 가전 위치·치수는 시공 환경에 따라 달라질 수 있습니다.
            </p>
          </div>
        )}

        {activeRoom && <RoomRenderCard room={activeRoom} showProducts={showProducts} />}
      </div>

      {/* 인쇄용(PDF): 모든 방을 펼쳐서 표시 (화면에서는 숨김) */}
      <div className='hidden print:block'>
        {rooms.map((room, idx) => {
          const appliances = appliancesMap?.[room.room_type] ?? []
          return (
            <section key={room.room_id} className='print-room'>
              {/* 첫 방 위에만 톤 요약(이름+팔레트)을 같은 페이지에 표시 */}
              {idx === 0 && tone && (
                <div className='mb-6 border-b border-stone-300 pb-4'>
                  <div className='flex items-baseline gap-2'>
                    <span
                      className='text-lg font-bold text-stone-900'
                      style={{ fontFamily: 'var(--font-serif)' }}
                    >
                      {tone.name}
                    </span>
                    <span className='text-xs text-stone-500'>{tone.category}</span>
                  </div>
                  <div className='mt-2 flex h-4 overflow-hidden rounded'>
                    {tone.color_palette.map((c, i) => (
                      <div key={i} className='flex-1' style={{ backgroundColor: c.hex }} />
                    ))}
                  </div>
                </div>
              )}
              <h3 className='mb-6 border-b border-stone-300 pb-1 text-base font-bold text-stone-900'>
                {room.room_type}
              </h3>
              {appliances.length > 0 && (
                <p className='mb-3 text-xs text-stone-500'>
                  <span className='font-semibold'>예상 배치 가전: </span>
                  {appliances.join(' · ')}
                </p>
              )}
              {/* PDF에는 렌더 이미지·추천 근거만 — 상품(URL·가격)은 제외 */}
              <RoomRenderCard room={room} showProducts={false} eager />
            </section>
          )
        })}
      </div>
    </div>
  )
}

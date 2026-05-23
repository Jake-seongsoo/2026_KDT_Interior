'use client'

import type { RoomResultOut } from '@/types/api'
import { RoomRenderCard } from './RoomRenderCard'

interface RoomTabsProps {
  rooms: RoomResultOut[]
  activeRoomId?: string | null
  onChange?: (roomId: string) => void
  /** 방 유형 → 배치 가전명 목록. 정밀화 시 선택된 가전이 있을 때만 전달. */
  appliancesMap?: Record<string, string[]>
}

export function RoomTabs({ rooms, activeRoomId, onChange, appliancesMap }: RoomTabsProps) {
  const activeIdx = activeRoomId
    ? rooms.findIndex(r => r.room_id === activeRoomId)
    : 0
  const resolvedIdx = activeIdx >= 0 ? activeIdx : 0
  const activeRoom = rooms[resolvedIdx]
  const activeAppliances = activeRoom ? (appliancesMap?.[activeRoom.room_type] ?? []) : []

  return (
    <div className='space-y-6'>
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

      {activeRoom && <RoomRenderCard room={activeRoom} />}
    </div>
  )
}

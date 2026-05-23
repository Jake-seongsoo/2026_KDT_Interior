'use client'

import type { RoomResultOut } from '@/types/api'
import { RoomRenderCard } from './RoomRenderCard'

interface RoomTabsProps {
  rooms: RoomResultOut[]
  activeRoomId?: string | null
  onChange?: (roomId: string) => void
}

export function RoomTabs({ rooms, activeRoomId, onChange }: RoomTabsProps) {
  const activeIdx = activeRoomId
    ? rooms.findIndex(r => r.room_id === activeRoomId)
    : 0
  const resolvedIdx = activeIdx >= 0 ? activeIdx : 0
  const activeRoom = rooms[resolvedIdx]

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

      {activeRoom && <RoomRenderCard room={activeRoom} />}
    </div>
  )
}

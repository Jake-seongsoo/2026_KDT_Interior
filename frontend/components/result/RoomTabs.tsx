'use client'

import type { RoomResultOut } from '@/types/api'
import { Button } from '@/components/ui/button'
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
  const activeRoom = rooms[activeIdx >= 0 ? activeIdx : 0]

  return (
    <div className='space-y-5'>
      <div className='flex gap-2 overflow-x-auto pb-1'>
        {rooms.map((room, i) => (
          <Button
            key={room.room_id}
            onClick={() => onChange?.(room.room_id)}
            variant={i === (activeIdx >= 0 ? activeIdx : 0) ? 'primary' : 'outline'}
            size='sm'
            className='shrink-0'
          >
            {room.room_type}
          </Button>
        ))}
      </div>

      {activeRoom && <RoomRenderCard room={activeRoom} />}
    </div>
  )
}

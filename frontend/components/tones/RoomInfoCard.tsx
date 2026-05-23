import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { RoomOut } from '@/types/api'

interface RoomInfoCardProps {
  rooms: RoomOut[]
}

export function RoomInfoCard({ rooms }: RoomInfoCardProps) {
  return (
    <Card>
      <CardHeader className='flex flex-row items-center justify-between'>
        <h2 className='text-sm font-semibold text-stone-900'>인식한 공간 구성</h2>
        <Badge variant='muted'>{rooms.length}개 공간</Badge>
      </CardHeader>
      <CardContent className='space-y-2.5'>
        {rooms.map((room, i) => (
          <div
            key={room.id}
            className='rounded-xl border border-stone-100 bg-stone-50 p-3'
          >
            <div className='flex items-center justify-between gap-3 mb-2'>
              <div className='flex min-w-0 items-center gap-2.5'>
                <span className='flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-stone-200 text-[11px] font-bold text-stone-600'>
                  {i + 1}
                </span>
                <div className='min-w-0'>
                  <p className='truncate text-sm font-semibold text-stone-900'>{room.room_type}</p>
                  {room.area_sqm && (
                    <p className='text-xs text-stone-400'>{room.area_sqm.toFixed(1)}㎡</p>
                  )}
                </div>
              </div>
              <span className='text-xs font-medium text-stone-400 shrink-0'>
                {Math.round(room.confidence * 100)}%
              </span>
            </div>
            <div className='h-1 overflow-hidden rounded-full bg-stone-200'>
              <div
                className='h-full rounded-full bg-amber-500 transition-all'
                style={{ width: `${Math.round(room.confidence * 100)}%` }}
              />
            </div>
          </div>
        ))}
        {rooms.some((r) => r.confidence < 0.65) && (
          <p className='rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-700'>
            일부 방의 인식 신뢰도가 낮습니다. 방 경계와 이름이 선명한 도면을 사용하면 정확도가 올라갑니다.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

import { Home } from 'lucide-react'
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
        <div className='flex items-center gap-2'>
          <Home className='h-4 w-4 text-teal-600' />
          <h2 className='text-sm font-bold text-slate-950'>인식한 방 구성</h2>
        </div>
        <Badge variant='success'>{rooms.length}개 공간</Badge>
      </CardHeader>
      <CardContent className='space-y-3'>
        {rooms.map((room, i) => (
          <div key={room.id} className='grid gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3 sm:grid-cols-[1fr_120px] sm:items-center'>
            <div className='flex min-w-0 items-center gap-3'>
              <span className='flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-bold text-slate-700 ring-1 ring-slate-200'>
                {i + 1}
              </span>
              <div className='min-w-0'>
                <p className='truncate text-sm font-semibold text-slate-900'>{room.room_type}</p>
                {room.area_sqm && (
                  <p className='text-xs text-slate-500'>{room.area_sqm.toFixed(1)}㎡</p>
                )}
              </div>
            </div>
            <div className='flex items-center gap-2'>
              <div className='h-2 flex-1 overflow-hidden rounded-full bg-slate-200'>
                <div
                  className='h-full rounded-full bg-teal-500'
                  style={{ width: `${Math.round(room.confidence * 100)}%` }}
                />
              </div>
              <span className='w-9 text-right text-xs font-medium text-slate-500'>
                {Math.round(room.confidence * 100)}%
              </span>
            </div>
          </div>
        ))}
        {rooms.some((r) => r.confidence < 0.65) && (
          <p className='rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-700'>
            일부 방의 인식 신뢰도가 낮습니다. 방 경계와 이름이 선명한 도면을 사용하면 정확도가 올라갑니다.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

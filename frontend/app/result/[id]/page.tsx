'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Home, Palette } from 'lucide-react'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, getRenderResult } from '@/lib/api'
import { LayoutCanvas } from '@/components/result/LayoutCanvas'
import { RoomTabs } from '@/components/result/RoomTabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { AnalyzeResponse, RenderResponse } from '@/types/api'

export default function ResultPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [data, setData] = useState<RenderResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [analyzeRooms, setAnalyzeRooms] = useState<AnalyzeResponse['rooms'] | null>(null)
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null)
  const roomTabsRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    let ignore = false

    const load = async () => {
      const sid = sessionStorage.getItem(`render_session:${id}`)
      if (sid) {
        setSessionId(sid)
        try {
          const analyzeRaw = sessionStorage.getItem(`analyze:${sid}`)
          if (analyzeRaw) {
            const parsed: AnalyzeResponse = JSON.parse(analyzeRaw)
            setAnalyzeRooms(parsed.rooms)
          }
        } catch {
          // 분석 데이터 없어도 무방 — 균등 분할 fallback
        }
      }

      const raw = sessionStorage.getItem(`render:${id}`)
      if (raw) {
        const parsed: RenderResponse = JSON.parse(raw)
        setData(parsed)
        setSelectedRoomId(parsed.room_results[0]?.room_id ?? null)
        return
      }

      try {
        const result = await getRenderResult(id)
        if (ignore) return
        sessionStorage.setItem(`render:${result.result_id}`, JSON.stringify(result))
        setData(result)
        setSelectedRoomId(result.room_results[0]?.room_id ?? null)
      } catch (e) {
        if (ignore) return
        if (e instanceof AuthRequiredError) {
          router.replace(`/auth/login?next=/result/${id}`)
          return
        }
        setError(e instanceof Error ? e.message : '결과를 불러오지 못했습니다.')
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [id, router])

  function handleRoomClick(roomId: string) {
    setSelectedRoomId(roomId)
    roomTabsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  if (error) {
    return (
      <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center px-4'>
        <div className='w-full max-w-md space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm'>
          <p className='rounded-lg border border-red-100 bg-red-50 p-4 text-sm text-red-700'>{error}</p>
          <Button asChild className='w-full'>
            <Link href='/'>새 도면 분석하기</Link>
          </Button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center'>
        <p className='text-sm text-slate-400'>불러오는 중...</p>
      </div>
    )
  }

  const tone = data.selected_tone

  return (
    <div className='mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6'>
      <section className='rounded-lg border border-slate-200 bg-slate-950 p-6 text-white shadow-sm'>
        <div className='flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between'>
          <div>
            <p className='mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-teal-300'>Selected tone</p>
            <h1 className='text-3xl font-bold tracking-tight'>{tone.name}</h1>
            <p className='mt-3 max-w-3xl text-sm leading-6 text-slate-300'>{tone.description}</p>
          </div>
          <div className='flex flex-col items-start gap-2 sm:items-end'>
            <Badge variant='success' className='w-fit bg-teal-400/10 text-teal-200'>
              {tone.category}
            </Badge>
            <div className='flex flex-col gap-2 sm:flex-row'>
              <Button asChild variant='outline' size='sm' className='border-white/20 bg-white/10 text-white hover:bg-white/20 hover:text-white'>
                <Link href='/'>
                  <Home className='h-4 w-4' />
                  홈으로
                </Link>
              </Button>
              {sessionId && (
                <Button asChild size='sm' className='bg-teal-500 text-white hover:bg-teal-400'>
                  <Link href={`/tones/${sessionId}`}>
                    <Palette className='h-4 w-4' />
                    다른 톤 선택
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </div>
        <div className='mt-6 flex flex-wrap gap-2'>
          {tone.color_palette.map((c, i) => (
            <div key={i} className='flex items-center gap-2 rounded-full bg-white/10 px-2 py-1'>
              <div
                title={c.name}
                className='h-5 w-5 rounded-full border border-white/30'
                style={{ backgroundColor: c.hex }}
              />
              <span className='text-xs text-slate-200'>{c.name}</span>
            </div>
          ))}
        </div>
      </section>

      <LayoutCanvas
        rooms={data.room_results.map(r => ({
          room_id: r.room_id,
          room_type: r.room_type,
          area_sqm: analyzeRooms?.find(ar => ar.id === r.room_id)?.area_sqm ?? null,
        }))}
        activeRoomId={selectedRoomId}
        onRoomClick={handleRoomClick}
      />

      <section ref={roomTabsRef} className='space-y-4 scroll-mt-4'>
        <div>
          <h2 className='text-xl font-bold text-slate-950'>방별 제안</h2>
          <p className='mt-1 text-sm text-slate-500'>공간별 렌더 이미지와 추천 근거, 상품 후보를 확인하세요.</p>
        </div>
        <RoomTabs
          rooms={data.room_results}
          activeRoomId={selectedRoomId}
          onChange={setSelectedRoomId}
        />
      </section>

      <div className='space-y-2 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-400'>
        <p>{data.disclaimer}</p>
        <p>처리 시간: {(data.processing_ms / 1000).toFixed(1)}초</p>
      </div>
    </div>
  )
}

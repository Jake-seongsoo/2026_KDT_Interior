'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Home, Palette, Settings2 } from 'lucide-react'
import { useParams, useRouter } from 'next/navigation'
import { AuthRequiredError, getRenderResult } from '@/lib/api'
import { ErrorScreen } from '@/components/common/ErrorScreen'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { LayoutCanvas } from '@/components/result/LayoutCanvas'
import { RoomTabs } from '@/components/result/RoomTabs'
import { RefinementModal } from '@/components/result/RefinementModal'
import { Button } from '@/components/ui/button'
import { analyzeStorage, renderStorage, toneStorage, refinementStorage } from '@/lib/session-storage'
import type { AnalyzeResponse, RefinementParams, RenderResponse } from '@/types/api'

const FAMILY_LABELS: Record<string, string> = {
  single: '1인 가구',
  couple: '커플·부부',
  family_with_kid: '아이와 함께',
  family_with_pet: '반려동물과 함께',
}

export default function ResultPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [data, setData] = useState<RenderResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [analyzeRooms, setAnalyzeRooms] = useState<AnalyzeResponse['rooms'] | null>(null)
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null)
  const [refinementOpen, setRefinementOpen] = useState(false)
  const [appliedRefinement, setAppliedRefinement] = useState<RefinementParams | null>(null)
  const roomTabsRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    let ignore = false

    const load = async () => {
      const sid = renderStorage.loadSessionId(id)
      if (sid) {
        setSessionId(sid)
        // 분석 데이터 없어도 무방 — 균등 분할 fallback
        const analyze = analyzeStorage.load(sid)
        if (analyze) setAnalyzeRooms(analyze.rooms)
        const refinement = refinementStorage.load(sid)
        if (refinement) setAppliedRefinement(refinement)
      }

      const cached = renderStorage.loadResult(id)
      if (cached) {
        setData(cached)
        setSelectedRoomId(cached.room_results[0]?.room_id ?? null)
        return
      }

      try {
        const result = await getRenderResult(id)
        if (ignore) return
        renderStorage.saveResult(result.result_id, result)
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

  function handleRefinementConfirm(params: RefinementParams) {
    if (!sessionId || !data) return
    const tone = data.selected_tone
    toneStorage.save(sessionId, tone)
    refinementStorage.save(sessionId, params)
    router.push(`/render/${sessionId}`)
  }

  if (error) return <ErrorScreen message={error} />
  if (!data) return <LoadingScreen />

  const tone = data.selected_tone

  return (
    <div className='min-h-[calc(100vh-4rem)] bg-ivory'>
      {/* 톤 히어로 — 다크 섹션 */}
      <section className='bg-stone-950'>
        <div className='mx-auto max-w-6xl px-4 py-10 sm:px-6'>
          <div className='flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between'>
            <div className='flex-1'>
              <p className='mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-amber-600'>
                Selected Tone
              </p>
              <h1
                className='text-3xl font-bold tracking-tight text-stone-100 sm:text-4xl'
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {tone.name}
              </h1>
              <p className='mt-3 max-w-2xl text-sm leading-7 text-stone-400'>
                {tone.description}
              </p>
            </div>
            <div className='flex items-center gap-2 sm:flex-col sm:items-end'>
              <span className='inline-flex h-6 items-center rounded-full border border-amber-700/40 bg-amber-700/20 px-2.5 text-xs font-medium text-amber-400'>
                {tone.category}
              </span>
              <div className='flex gap-2 mt-2'>
                <Button
                  asChild
                  variant='outline'
                  size='sm'
                  className='border-stone-700 bg-stone-800 text-stone-300 hover:bg-stone-700 hover:text-stone-100'
                >
                  <Link href='/'>
                    <Home className='h-4 w-4' />
                    홈으로
                  </Link>
                </Button>
                {sessionId && (
                  <>
                    <Button
                      asChild
                      variant='outline'
                      size='sm'
                      className='border-stone-700 bg-stone-800 text-stone-300 hover:bg-stone-700 hover:text-stone-100'
                    >
                      <Link href={`/tones/${sessionId}`}>
                        <Palette className='h-4 w-4' />
                        다른 톤
                      </Link>
                    </Button>
                    <Button
                      size='sm'
                      className='bg-amber-700 text-white hover:bg-amber-600'
                      onClick={() => setRefinementOpen(true)}
                    >
                      <Settings2 className='h-4 w-4' />
                      정밀화
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* 정밀화 조건 배지 */}
          {appliedRefinement && (() => {
            const chips: string[] = []
            if (appliedRefinement.budget_10k_won)
              chips.push(`예산 ${appliedRefinement.budget_10k_won.toLocaleString()}만원`)
            if (appliedRefinement.family_type)
              chips.push(FAMILY_LABELS[appliedRefinement.family_type] ?? appliedRefinement.family_type)
            if (appliedRefinement.style_keywords?.length)
              chips.push(...appliedRefinement.style_keywords)
            if (appliedRefinement.keep_appliances)
              chips.push('기존 가전 유지')
            const hasChips = chips.length > 0
            const userText = appliedRefinement.user_text?.trim()
            if (!hasChips && !userText) return null
            return (
              <div className='mt-5 space-y-2'>
                {hasChips && (
                  <div className='flex flex-wrap items-center gap-2'>
                    <span className='text-xs font-semibold uppercase tracking-widest text-stone-500'>
                      적용된 조건
                    </span>
                    {chips.map(chip => (
                      <span
                        key={chip}
                        className='inline-flex items-center rounded-full border border-amber-700/40 bg-amber-700/20 px-2.5 py-0.5 text-xs font-medium text-amber-400'
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                )}
                {userText && (
                  <div className='rounded-lg border border-amber-700/30 bg-amber-900/10 px-4 py-3'>
                    <p className='mb-1 text-[10px] font-semibold uppercase tracking-widest text-stone-500'>
                      추가 요청사항
                    </p>
                    <p className='text-sm italic text-stone-300'>"{userText}"</p>
                  </div>
                )}
              </div>
            )
          })()}

          {/* 팔레트 바 */}
          <div className='mt-8 overflow-hidden rounded-xl' style={{ height: 48 }}>
            <div className='flex h-full'>
              {tone.color_palette.map((c, i) => (
                <div
                  key={i}
                  title={c.name}
                  className='flex-1 relative group'
                  style={{ backgroundColor: c.hex }}
                >
                  <span className='absolute bottom-0 left-0 right-0 bg-black/50 py-0.5 text-center text-[9px] text-white opacity-0 group-hover:opacity-100 transition-opacity'>
                    {c.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 메인 콘텐츠 */}
      <div className='mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6'>
        {/* 배치도 */}
        <LayoutCanvas
          rooms={data.room_results.map(r => ({
            room_id: r.room_id,
            room_type: r.room_type,
            area_sqm: analyzeRooms?.find(ar => ar.id === r.room_id)?.area_sqm ?? null,
          }))}
          activeRoomId={selectedRoomId}
          onRoomClick={handleRoomClick}
        />

        {/* 방별 제안 */}
        <section ref={roomTabsRef} className='scroll-mt-4'>
          <div className='mb-5'>
            <h2
              className='text-xl font-bold text-stone-900'
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              방별 제안
            </h2>
            <p className='mt-1 text-sm text-stone-500'>
              공간별 렌더 이미지와 추천 근거, 상품 후보를 확인하세요.
            </p>
          </div>
          <RoomTabs
            rooms={data.room_results}
            activeRoomId={selectedRoomId}
            onChange={setSelectedRoomId}
            appliancesMap={(() => {
              const list = appliedRefinement?.appliances
              if (!list || list.length === 0) return undefined
              return list.reduce<Record<string, string[]>>((acc, a) => {
                acc[a.room] = [...(acc[a.room] ?? []), a.name]
                return acc
              }, {})
            })()}
          />
        </section>

        {/* 푸터 면책 */}
        <div className='space-y-2 border-t border-stone-200 pt-5 text-xs leading-5 text-stone-400'>
          <p>{data.disclaimer}</p>
          <p>처리 시간: {(data.processing_ms / 1000).toFixed(1)}초</p>
        </div>
      </div>

      <RefinementModal
        open={refinementOpen}
        onOpenChange={setRefinementOpen}
        onConfirm={handleRefinementConfirm}
        rooms={data.room_results.map(r => r.room_type)}
      />
    </div>
  )
}

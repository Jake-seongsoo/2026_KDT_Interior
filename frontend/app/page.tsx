'use client'

import { useRouter } from 'next/navigation'
import { FloorPlanUploader } from '@/components/upload/FloorPlanUploader'
import { createClient } from '@/lib/supabase/client'

export default function HomePage() {
  const router = useRouter()

  const ensureLoggedIn = async () => {
    const supabase = createClient()
    const { data } = await supabase.auth.getSession()

    if (!data.session) {
      alert('도면 업로드와 AI 분석을 진행하려면 먼저 로그인이 필요합니다.')
      router.push('/auth/login?next=/')
      return false
    }

    return true
  }

  const handleUpload = async (file: File, floorAreaPyeong: number) => {
    if (!(await ensureLoggedIn())) {
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      const base64 = e.target?.result as string
      sessionStorage.setItem('upload:file:base64', base64)
      sessionStorage.setItem('upload:file:name', file.name)
      sessionStorage.setItem('upload:file:type', file.type)
      sessionStorage.setItem('upload:floorArea', String(floorAreaPyeong))
      router.push('/analyze')
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className='min-h-[calc(100vh-4rem)] bg-[#F5EFE5]'>
      <div className='mx-auto grid max-w-6xl gap-12 px-4 py-12 sm:px-6 lg:grid-cols-[1fr_420px] lg:py-20 lg:gap-16 lg:items-start'>

        {/* 좌측: 헤드라인 + 설명 */}
        <section className='lg:pt-4'>
          <p
            className='mb-5 text-xs font-semibold uppercase tracking-[0.2em] text-amber-700'
          >
            2026 인테리어 톤 추천
          </p>

          <h1
            className='text-4xl font-bold leading-[1.2] tracking-tight text-stone-900 sm:text-5xl lg:text-6xl'
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            도면 한 장으로
            <br />
            <span className='text-stone-400'>공간의 방향을</span>
            <br />
            읽습니다.
          </h1>

          <p className='mt-6 max-w-lg text-base leading-8 text-stone-500'>
            AI가 평면도를 분석해 공간 구성을 파악하고, 어울리는 톤과 방별 연출안, 추천 가구까지 한 흐름으로 제안합니다.
          </p>

          {/* 스텝 표시 */}
          <div className='mt-10 space-y-4'>
            {[
              { step: '01', label: '도면 업로드', desc: '분양 도면이나 네이버 부동산 캡처' },
              { step: '02', label: '방 구성 분석', desc: 'Claude Vision으로 공간 인식' },
              { step: '03', label: '인테리어 톤 선택', desc: '2026 트렌드 기반 6가지 팔레트' },
              { step: '04', label: '방별 제안 확인', desc: 'Imagen 렌더링 + 이케아 추천 상품' },
            ].map(({ step, label, desc }) => (
              <div key={step} className='flex items-start gap-4'>
                <span
                  className='mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-stone-900 text-[11px] font-bold text-amber-100'
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {step}
                </span>
                <div>
                  <p className='text-sm font-semibold text-stone-800'>{label}</p>
                  <p className='text-xs text-stone-400 mt-0.5'>{desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className='mt-10 h-px w-24 bg-stone-300' />

          <p className='mt-6 text-xs leading-6 text-stone-400 max-w-sm'>
            아파트 분양 도면·네이버 부동산 캡처에 최적화. 방 경계와 이름이 선명한 이미지를 사용하세요.
          </p>
        </section>

        {/* 우측: 업로드 카드 */}
        <div className='rounded-2xl border border-stone-200 bg-white p-6 shadow-sm sm:p-7'>
          <div className='mb-6'>
            <h2
              className='text-xl font-semibold text-stone-900'
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              도면 업로드
            </h2>
            <p className='mt-1.5 text-sm text-stone-400'>공급면적과 도면 이미지를 입력해 주세요.</p>
          </div>
          <FloorPlanUploader onSubmit={handleUpload} onBeforeFileSelect={ensureLoggedIn} />
        </div>

      </div>
    </div>
  )
}

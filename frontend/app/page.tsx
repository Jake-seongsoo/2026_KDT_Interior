'use client'

import { useRouter } from 'next/navigation'
import { ArrowRight, CheckCircle2 } from 'lucide-react'
import { FloorPlanUploader } from '@/components/upload/FloorPlanUploader'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
    <div className='min-h-[calc(100vh-4rem)] bg-[radial-gradient(circle_at_top_left,#ccfbf1,transparent_32rem),linear-gradient(180deg,#ffffff,#f8fafc)]'>
      <div className='mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_440px] lg:py-16'>
        <section className='flex flex-col justify-center'>
          <Badge variant='success' className='mb-5 w-fit'>
            2026 인테리어 톤 추천
          </Badge>
          <h1 className='max-w-2xl text-4xl font-bold leading-tight tracking-tight text-slate-950 sm:text-5xl'>
            도면 한 장으로 방별 인테리어 방향을 빠르게 잡습니다.
          </h1>
          <p className='mt-5 max-w-xl text-base leading-7 text-slate-600'>
            AI가 평면도를 읽고 공간 구성을 파악한 뒤, 어울리는 톤과 방별 연출안, 추천 상품 후보까지 한 흐름으로 제안합니다.
          </p>
          <div className='mt-8 grid gap-3 text-sm text-slate-700 sm:grid-cols-3'>
            {['방 구성 분석', '톤 팔레트 추천', '방별 렌더 제안'].map((item) => (
              <div key={item} className='flex items-center gap-2'>
                <CheckCircle2 className='h-4 w-4 text-teal-600' />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <div className='mt-10 flex items-center gap-2 text-sm font-medium text-slate-500'>
            <span>도면을 올리면 바로 분석 단계로 이동합니다.</span>
            <ArrowRight className='h-4 w-4' />
          </div>
        </section>

        <Card className='self-start'>
          <CardContent className='p-5 sm:p-6'>
            <div className='mb-5'>
              <h2 className='text-lg font-bold text-slate-950'>도면 업로드</h2>
              <p className='mt-1 text-sm text-slate-500'>공급면적과 도면 이미지를 입력해 주세요.</p>
            </div>
            <FloorPlanUploader onSubmit={handleUpload} onBeforeFileSelect={ensureLoggedIn} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

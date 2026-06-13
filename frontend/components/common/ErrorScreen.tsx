import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface ErrorScreenProps {
  message: string
}

/** 전체 화면 에러 카드 — 데이터 로드 실패 시 새 분석 시작 유도 */
export function ErrorScreen({ message }: ErrorScreenProps) {
  return (
    <div className='flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 bg-ivory'>
      <div className='w-full max-w-md space-y-4 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm'>
        <p className='rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700'>{message}</p>
        <Button asChild className='w-full'>
          <Link href='/'>새 도면 분석하기</Link>
        </Button>
      </div>
    </div>
  )
}

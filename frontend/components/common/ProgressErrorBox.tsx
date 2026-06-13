import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface ProgressErrorBoxProps {
  message: string
  actionHref: string
  actionLabel: string
}

/** 진행 대기 페이지(다크 배경)용 에러 박스 + 복귀 버튼 */
export function ProgressErrorBox({ message, actionHref, actionLabel }: ProgressErrorBoxProps) {
  return (
    <div className='space-y-4'>
      <p className='rounded-xl border border-red-900/30 bg-red-950/40 p-4 text-sm text-red-300'>
        {message}
      </p>
      <Button asChild className='w-full bg-stone-700 text-white hover:bg-stone-600'>
        <Link href={actionHref}>{actionLabel}</Link>
      </Button>
    </div>
  )
}

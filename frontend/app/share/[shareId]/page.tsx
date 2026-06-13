import { cache } from 'react'
import type { Metadata } from 'next'
import { getSharedResult } from '@/lib/api'
import { ErrorScreen } from '@/components/common/ErrorScreen'
import { SharedResultView } from '@/components/share/SharedResultView'

// generateMetadata와 page가 같은 렌더에서 1회만 호출하도록 dedupe → view_count 1회 증가
const fetchShared = cache((shareId: string) => getSharedResult(shareId))

interface SharePageProps {
  params: Promise<{ shareId: string }>
}

export async function generateMetadata({ params }: SharePageProps): Promise<Metadata> {
  try {
    const { shareId } = await params
    const data = await fetchShared(shareId)
    const title = `${data.selected_tone.name} 인테리어 제안`
    const firstImg = data.room_results.find(r => r.render_url)?.render_url
    return {
      title,
      description: data.selected_tone.description,
      openGraph: {
        title,
        description: data.selected_tone.description,
        images: firstImg ? [firstImg] : [],
      },
    }
  } catch {
    return { title: '공유된 인테리어 제안' }
  }
}

export default async function SharePage({ params }: SharePageProps) {
  const { shareId } = await params

  let data
  try {
    data = await fetchShared(shareId)
  } catch {
    return <ErrorScreen message='공유 링크를 찾을 수 없거나 만료되었습니다.' />
  }

  return <SharedResultView data={data} />
}

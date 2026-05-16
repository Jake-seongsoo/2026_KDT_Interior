import { Map } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

interface SvgLayoutViewerProps {
  svgContent: string
}

export function SvgLayoutViewer({ svgContent }: SvgLayoutViewerProps) {
  return (
    <Card className='overflow-hidden'>
      <CardHeader className='flex flex-row items-center gap-2'>
        <Map className='h-4 w-4 text-teal-600' />
        <h2 className='text-sm font-bold text-slate-950'>2D 공간 배치도</h2>
      </CardHeader>
      <CardContent>
        <div
          className='flex items-center justify-center overflow-auto rounded-lg bg-slate-50 p-4'
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />
      </CardContent>
    </Card>
  )
}

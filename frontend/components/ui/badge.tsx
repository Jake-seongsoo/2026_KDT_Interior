import * as React from 'react'
import { cn } from '@/lib/utils'

type BadgeVariant = 'default' | 'muted' | 'success' | 'warning'

const variants: Record<BadgeVariant, string> = {
  default: 'border-stone-900 bg-stone-900 text-white',
  muted: 'border-stone-200 bg-stone-100 text-stone-600',
  success: 'border-amber-200 bg-amber-50 text-amber-800',
  warning: 'border-amber-300 bg-amber-100 text-amber-800',
}

export function Badge({
  className,
  variant = 'muted',
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center rounded-full border px-2.5 text-xs font-medium tracking-wide',
        variants[variant],
        className,
      )}
      {...props}
    />
  )
}

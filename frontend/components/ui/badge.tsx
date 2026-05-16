import * as React from 'react'
import { cn } from '@/lib/utils'

type BadgeVariant = 'default' | 'muted' | 'success' | 'warning'

const variants: Record<BadgeVariant, string> = {
  default: 'border-slate-200 bg-slate-950 text-white',
  muted: 'border-slate-200 bg-slate-100 text-slate-700',
  success: 'border-teal-200 bg-teal-50 text-teal-700',
  warning: 'border-amber-200 bg-amber-50 text-amber-700',
}

export function Badge({
  className,
  variant = 'muted',
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center rounded-full border px-2.5 text-xs font-medium',
        variants[variant],
        className,
      )}
      {...props}
    />
  )
}

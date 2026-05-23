import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          'flex w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm',
          'text-stone-900 placeholder:text-stone-400',
          'focus:outline-none focus:ring-2 focus:ring-stone-400 focus:ring-offset-1',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'resize-none',
          className,
        )}
        {...props}
      />
    )
  },
)

Textarea.displayName = 'Textarea'

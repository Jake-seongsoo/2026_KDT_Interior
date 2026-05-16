import * as React from 'react'
import { cn } from '@/lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  asChild?: boolean
}

const variants: Record<ButtonVariant, string> = {
  primary:
    'bg-slate-950 text-white shadow-sm hover:bg-slate-800 focus-visible:ring-slate-400 disabled:bg-slate-300 disabled:text-slate-500',
  secondary:
    'bg-teal-600 text-white shadow-sm hover:bg-teal-500 focus-visible:ring-teal-300 disabled:bg-slate-300 disabled:text-slate-500',
  outline:
    'border border-slate-200 bg-white text-slate-700 shadow-sm hover:border-slate-300 hover:bg-slate-50 focus-visible:ring-slate-300',
  ghost:
    'text-slate-600 hover:bg-slate-100 hover:text-slate-950 focus-visible:ring-slate-300',
  danger:
    'bg-red-600 text-white shadow-sm hover:bg-red-500 focus-visible:ring-red-300 disabled:bg-slate-300',
}

const sizes: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', type = 'button', asChild, children, ...props }, ref) => {
    const classes = cn(
      'inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      'disabled:pointer-events-none disabled:cursor-not-allowed',
      variants[variant],
      sizes[size],
      className,
    )

    if (asChild && React.isValidElement<{ className?: string }>(children)) {
      return React.cloneElement(children, {
        className: cn(classes, children.props.className),
      })
    }

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        {...props}
      >
        {children}
      </button>
    )
  },
)

Button.displayName = 'Button'

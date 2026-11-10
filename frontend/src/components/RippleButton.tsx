import {
  type ButtonHTMLAttributes,
  type LabelHTMLAttributes,
  type MouseEvent,
  useRef,
} from 'react'

type Variant = 'primary' | 'ghost'

function spawnRipple(target: HTMLElement, event: MouseEvent<HTMLElement>, variant: Variant) {
  const rect = target.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height) * 1.2
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2
  const ripple = document.createElement('span')
  ripple.className = `ui-ripple ${variant === 'primary' ? 'ui-ripple-light' : 'ui-ripple-dark'}`
  ripple.style.width = `${size}px`
  ripple.style.height = `${size}px`
  ripple.style.left = `${x}px`
  ripple.style.top = `${y}px`
  target.appendChild(ripple)
  window.setTimeout(() => ripple.remove(), 600)
}

export function RippleButton({
  variant = 'ghost',
  className = '',
  children,
  onMouseDown,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const ref = useRef<HTMLButtonElement>(null)
  return (
    <button
      {...props}
      ref={ref}
      className={`ui-btn ${variant === 'primary' ? 'ui-btn-primary' : 'ui-btn-ghost'} ${className}`}
      onMouseDown={(e) => {
        if (!props.disabled && ref.current) spawnRipple(ref.current, e, variant)
        onMouseDown?.(e)
      }}
    >
      <span className="ui-btn-label">{children}</span>
    </button>
  )
}

export function RippleLabel({
  variant = 'ghost',
  className = '',
  children,
  onMouseDown,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement> & { variant?: Variant }) {
  const ref = useRef<HTMLLabelElement>(null)
  return (
    <label
      {...props}
      ref={ref}
      className={`ui-btn ${variant === 'primary' ? 'ui-btn-primary' : 'ui-btn-ghost'} ${className}`}
      onMouseDown={(e) => {
        if (ref.current) spawnRipple(ref.current, e, variant)
        onMouseDown?.(e)
      }}
    >
      <span className="ui-btn-label">{children}</span>
    </label>
  )
}

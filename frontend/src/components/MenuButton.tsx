import { useCallback, useRef, useState } from 'react'
import { useDismiss } from '../lib/useDismiss'
import Icon from './Icon'

type Props<T extends string> = {
  value: T
  options: { value: T; label: string }[]
  onChange: (value: T) => void
}

/** A toolbar dropdown like "Today trips ▾" or "All contracts ▾". */
export default function MenuButton<T extends string>({ value, options, onChange }: Props<T>) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const close = useCallback(() => setOpen(false), [])
  useDismiss(ref, open, close)
  const current = options.find((o) => o.value === value)

  return (
    <div className="pop-anchor" ref={ref}>
      <button
        type="button"
        className="tbtn tdrop"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {current?.label}
        <Icon name="chevron" className="chev" strokeWidth={2} />
      </button>
      {open && (
        <div className="dpop narrow" role="menu">
          {options.map((o) => (
            <button
              key={o.value}
              type="button"
              role="menuitemradio"
              aria-checked={o.value === value}
              className="dpopt"
              data-sel={o.value === value}
              onClick={() => {
                onChange(o.value)
                close()
              }}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

import { useCallback, useRef, useState } from 'react'
import type { Terminal } from '../api/types'
import Icon from '../components/Icon'
import { useDismiss } from '../lib/useDismiss'

type Props = {
  terminals: Terminal[]
  selected: string[]
  label: string
  onChange: (codes: string[]) => void
}

/**
 * "Terminal: All ▾" popover (R27). "All terminals" checks every box when it is
 * off and clears every box when it is on; it shows checked only when every
 * terminal is checked.
 */
export default function TerminalFilter({ terminals, selected, label, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const close = useCallback(() => setOpen(false), [])
  useDismiss(ref, open, close)

  const all = terminals.length > 0 && terminals.every((t) => selected.includes(t.code))
  const toggleAll = () => onChange(all ? [] : terminals.map((t) => t.code))
  const toggle = (code: string) => {
    const next = selected.includes(code) ? selected.filter((c) => c !== code) : [...selected, code]
    // Keep the reference order so labels read NJ, NY, PA… not click order.
    onChange(terminals.map((t) => t.code).filter((c) => next.includes(c)))
  }

  return (
    <div className="pop-anchor" ref={ref}>
      <button
        type="button"
        className="tbtn tdrop"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        Terminal: {label}
        <Icon name="chevron" className="chev" strokeWidth={2} />
      </button>
      {open && (
        <div className="dpop" role="dialog" aria-label="Show terminals">
          <div className="dptitle">Show terminals</div>
          <label className="chk">
            <input type="checkbox" checked={all} onChange={toggleAll} />
            All terminals
          </label>
          <div className="dpdiv" />
          {terminals.map((t) => (
            <label key={t.code} className="chk">
              <input
                type="checkbox"
                checked={selected.includes(t.code)}
                onChange={() => toggle(t.code)}
              />
              {t.code} – {t.name}
            </label>
          ))}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 6 }}>
            <button type="button" className="btn2" onClick={close}>
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

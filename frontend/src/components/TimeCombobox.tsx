import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import { useDismiss } from '../lib/useDismiss'
import { matchTimes, normalizeTime, ONE_WAY, TIME_LIST } from '../lib/time'
import Icon from './Icon'

type Props = {
  id: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  oneWay?: boolean
  invalid?: boolean
}

/**
 * Text input with a dropdown of every 15 minutes (docs/UI_GUIDE.md):
 * typing digits filters by prefix and highlights the first match, Enter picks
 * the highlight, the list scrolls to the current value when opened, and
 * leaving the field normalizes what was typed (R02). The server re-checks.
 */
export default function TimeCombobox({ id, value, onChange, placeholder, oneWay, invalid }: Props) {
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState<string | null>(null)
  const [hl, setHl] = useState(-1)
  const wrap = useRef<HTMLDivElement>(null)
  const list = useRef<HTMLDivElement>(null)
  const listId = useId()
  const close = useCallback(() => {
    setOpen(false)
    setFilter(null)
  }, [])
  useDismiss(wrap, open, close)

  const options = useMemo(() => {
    if (filter === null) return oneWay ? [ONE_WAY, ...TIME_LIST] : TIME_LIST
    return /^\s*o/i.test(filter) && oneWay ? [ONE_WAY] : matchTimes(filter, TIME_LIST)
  }, [filter, oneWay])

  // Scroll the highlighted (or current) option into view when the list changes.
  useEffect(() => {
    if (!open || !list.current) return
    const index = hl >= 0 ? hl : options.indexOf(value)
    const el = list.current.children[index] as HTMLElement | undefined
    if (el && typeof el.scrollIntoView === 'function') el.scrollIntoView({ block: 'nearest' })
  }, [open, hl, options, value])

  const pick = (option: string) => {
    onChange(option)
    close()
  }
  const commit = () => {
    const normalized = normalizeTime(value, oneWay)
    if (normalized !== null && normalized !== value) onChange(normalized)
  }

  return (
    <div className="combo" ref={wrap}>
      <input
        id={id}
        type="text"
        className="field"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-invalid={invalid || undefined}
        aria-activedescendant={open && hl >= 0 ? `${listId}-${hl}` : undefined}
        autoComplete="off"
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          const text = e.target.value
          onChange(text)
          setFilter(text)
          setOpen(true)
          const matches = /^\s*o/i.test(text) && oneWay ? [ONE_WAY] : matchTimes(text, TIME_LIST)
          setHl(text.trim() && matches.length ? 0 : -1)
        }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') {
            e.preventDefault()
            setOpen(true)
            setHl((h) => Math.min(options.length - 1, h + 1))
          } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setHl((h) => Math.max(0, h - 1))
          } else if (e.key === 'Enter') {
            if (open && hl >= 0 && options[hl]) {
              e.preventDefault()
              pick(options[hl])
            } else commit()
          } else if (e.key === 'Escape') close()
        }}
        onBlur={(e) => {
          if (!wrap.current?.contains(e.relatedTarget as Node)) {
            commit()
            close()
          }
        }}
      />
      <button
        type="button"
        className="combobtn"
        tabIndex={-1}
        aria-label="Show times"
        onClick={() => {
          setFilter(null)
          setHl(-1)
          setOpen((o) => !o)
        }}
      >
        <Icon name="chevron" size={14} strokeWidth={2} />
      </button>
      {open && options.length > 0 && (
        <div className="combolist" role="listbox" id={listId} ref={list}>
          {options.map((option, i) => (
            <button
              key={option}
              id={`${listId}-${i}`}
              type="button"
              role="option"
              tabIndex={-1}
              aria-selected={option === value}
              className="comboopt"
              data-hl={i === hl}
              data-sel={option === value}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => pick(option)}
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { normalizeInitials } from '../lib/initials'

type Props = {
  value: string
  label: string
  onFocus: () => void
  onSave: (initials: string) => void
}

/** Initials cell: saves shortly after typing stops, or on blur. */
export default function InitialsInput({ value, label, onFocus, onSave }: Props) {
  const [draft, setDraft] = useState(value)
  const [editing, setEditing] = useState(false)
  const timer = useRef<number | undefined>(undefined)
  const shown = editing ? draft : value

  useEffect(() => () => window.clearTimeout(timer.current), [])

  const flush = (next: string) => {
    window.clearTimeout(timer.current)
    if (next !== value) onSave(next)
  }

  return (
    <input
      type="text"
      className="initin"
      maxLength={8}
      placeholder="Add"
      aria-label={label}
      value={shown}
      onFocus={() => {
        setDraft(value)
        setEditing(true)
        onFocus()
      }}
      onChange={(e) => {
        const next = normalizeInitials(e.target.value)
        setDraft(next)
        window.clearTimeout(timer.current)
        timer.current = window.setTimeout(() => flush(next), 600)
      }}
      onBlur={() => {
        flush(draft)
        setEditing(false)
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') e.currentTarget.blur()
      }}
      onClick={(e) => e.stopPropagation()}
    />
  )
}

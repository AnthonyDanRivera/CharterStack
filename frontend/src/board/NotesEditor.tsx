import { useEffect, useRef, useState } from 'react'
import type { UnitDetail } from '../api/types'

/** Dispatch notes save as you type (debounced PATCH, R23). */
export default function NotesEditor({
  unit,
  onNotes,
}: {
  unit: UnitDetail
  onNotes: (n: string) => void
}) {
  const [draft, setDraft] = useState(unit.dispatch_notes)
  const timer = useRef<number | undefined>(undefined)
  const latest = useRef(draft)
  const saved = useRef(unit.dispatch_notes)

  useEffect(
    () => () => {
      window.clearTimeout(timer.current)
      if (latest.current !== saved.current) onNotes(latest.current)
    },
    // Flush once on unmount only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  return (
    <div className="fld">
      <label htmlFor="dispatch-notes" className="ibox-title">
        Dispatch notes
      </label>
      <textarea
        id="dispatch-notes"
        className="field tarea"
        style={{ minHeight: 140 }}
        placeholder="Add notes for dispatch"
        value={draft}
        maxLength={2000}
        onChange={(e) => {
          const next = e.target.value
          setDraft(next)
          latest.current = next
          window.clearTimeout(timer.current)
          timer.current = window.setTimeout(() => {
            saved.current = next
            onNotes(next)
          }, 500)
        }}
      />
      <p className="hint">Notes save automatically as you type.</p>
    </div>
  )
}

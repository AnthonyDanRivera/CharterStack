import { useState } from 'react'
import type { BoardRow } from '../api/types'

type Props = {
  selected: BoardRow | null
  busy: boolean
  onReported: () => void
  onOnLocation: () => void
  onCancel: () => void
  onDuplicate: () => void
  onDeleteDuplicate: () => void
  onExport: () => void
  onResetColumns: () => void
}

/** Buttons under the table. Delete duplicate takes two clicks (R16). */
export default function ActionBar(props: Props) {
  const { selected, busy } = props
  const [armedFor, setArmedFor] = useState<number | null>(null)
  const armed = selected !== null && armedFor === selected.id
  const none = selected === null || busy
  const reported = selected?.actual_report_time ?? null
  const onloc = selected?.status === 'onloc'
  const cancelled = selected?.status === 'cancelled'

  return (
    <div className="bbar">
      <div className="tgroup bgroup">
        <button
          type="button"
          className="tbtn st-rep"
          data-on={reported !== null}
          aria-pressed={reported !== null}
          disabled={none}
          onClick={props.onReported}
        >
          {reported ? `Reported ${reported}` : 'Reported'}
        </button>
        <button
          type="button"
          className="tbtn st-onloc"
          data-on={onloc}
          aria-pressed={onloc}
          disabled={none}
          onClick={props.onOnLocation}
        >
          <span className="sw" aria-hidden="true" />
          On location
        </button>
        <button
          type="button"
          className="tbtn st-cxl"
          data-on={cancelled}
          aria-pressed={cancelled}
          disabled={none}
          onClick={props.onCancel}
        >
          <span className="sw" aria-hidden="true" />
          Cancelled
        </button>
        <button type="button" className="tbtn" disabled={none} onClick={props.onDuplicate}>
          Duplicate
        </button>
        <button
          type="button"
          className="tbtn tdel"
          data-armed={armed ? '2' : undefined}
          disabled={none || !selected?.is_duplicate}
          onClick={() => {
            if (!selected) return
            if (armed) {
              setArmedFor(null)
              props.onDeleteDuplicate()
            } else setArmedFor(selected.id)
          }}
          onBlur={() => setArmedFor(null)}
        >
          {armed ? 'Click again to delete' : 'Delete duplicate'}
        </button>
        <span className="tsep" aria-hidden="true" />
        <button type="button" className="tbtn" onClick={props.onExport}>
          Export to Excel
        </button>
      </div>
      <div className="tgroup bgroup">
        <button type="button" className="tbtn" onClick={props.onResetColumns}>
          Reset columns
        </button>
      </div>
    </div>
  )
}

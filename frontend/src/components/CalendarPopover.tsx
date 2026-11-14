import { useState } from 'react'
import { addDays, MONTH_NAMES, toDate, toIso, todayIso } from '../lib/dates'
import Icon from './Icon'

type Props = {
  target: 'start' | 'end'
  start: string
  end: string
  onPick: (iso: string) => void
  onToday: () => void
}

/** Month grid with the selected range tinted and its ends solid blue. */
export default function CalendarPopover({ target, start, end, onPick, onToday }: Props) {
  const anchor = toDate(target === 'start' ? start : end)
  const [view, setView] = useState({ y: anchor.getUTCFullYear(), m: anchor.getUTCMonth() })
  const today = todayIso()

  const first = new Date(Date.UTC(view.y, view.m, 1))
  const lead = first.getUTCDay()
  const daysInMonth = new Date(Date.UTC(view.y, view.m + 1, 0)).getUTCDate()
  const cells: (string | null)[] = [
    ...Array.from({ length: lead }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => addDays(toIso(first), i)),
  ]

  const rangeOf = (iso: string) => {
    if (start === end && iso === start) return 'single'
    if (iso === start) return 'start'
    if (iso === end) return 'end'
    if (iso > start && iso < end) return 'mid'
    return undefined
  }
  const move = (delta: number) => {
    const d = new Date(Date.UTC(view.y, view.m + delta, 1))
    setView({ y: d.getUTCFullYear(), m: d.getUTCMonth() })
  }

  return (
    <div
      className="calpop"
      role="dialog"
      aria-label={target === 'start' ? 'Start date' : 'End date'}
    >
      <div className="calhead">
        <button
          type="button"
          className="calnav"
          onClick={() => move(-1)}
          aria-label="Previous month"
        >
          <Icon name="left" size={18} />
        </button>
        <span>
          {MONTH_NAMES[view.m]} {view.y}
        </span>
        <button type="button" className="calnav" onClick={() => move(1)} aria-label="Next month">
          <Icon name="right" size={18} />
        </button>
      </div>
      <p className="calhint">
        {target === 'start' ? 'Pick a date to go to it' : 'Pick the last date of the range'}
      </p>
      <div className="calgrid">
        {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map((d) => (
          <span key={d} className="calwd">
            {d}
          </span>
        ))}
        {cells.map((iso, i) =>
          iso === null ? (
            <button key={`b${i}`} type="button" className="calday" data-blank="true" disabled />
          ) : (
            <button
              key={iso}
              type="button"
              className="calday"
              data-range={rangeOf(iso)}
              data-today={iso === today && !rangeOf(iso) ? 'true' : undefined}
              aria-label={iso}
              aria-pressed={rangeOf(iso) !== undefined}
              onClick={() => onPick(iso)}
            >
              {Number(iso.slice(8, 10))}
            </button>
          ),
        )}
      </div>
      <div className="calfoot">
        <button type="button" className="callink" onClick={onToday}>
          Today
        </button>
      </div>
    </div>
  )
}

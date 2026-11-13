import { useCallback, useRef, useState } from 'react'
import { fmtLong, shiftRange, todayIso } from '../lib/dates'
import { useDismiss } from '../lib/useDismiss'
import CalendarPopover from './CalendarPopover'
import Icon from './Icon'

export type DateRange = { start: string; end: string }

/** ‹ Start/End date › Today. Shared by the Dispatch board and Booking tabs. */
export default function DateRangeControl({
  range,
  onChange,
}: {
  range: DateRange
  onChange: (range: DateRange) => void
}) {
  const [open, setOpen] = useState<'start' | 'end' | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const close = useCallback(() => setOpen(null), [])
  useDismiss(ref, open !== null, close)

  const goToday = () => {
    const t = todayIso()
    onChange({ start: t, end: t })
    setOpen(null)
  }
  const pick = (iso: string) => {
    if (open === 'start') {
      // Picking a start after the current end collapses to that single day.
      onChange({ start: iso, end: iso > range.end ? iso : range.end })
    } else if (iso < range.start) {
      onChange({ start: iso, end: iso })
    } else {
      onChange({ start: range.start, end: iso })
    }
    setOpen(null)
  }
  const toggle = (which: 'start' | 'end') => setOpen((cur) => (cur === which ? null : which))

  return (
    <div className="tgroup">
      <button
        type="button"
        className="tbtn icon"
        aria-label="Previous period"
        onClick={() => onChange(shiftRange(range.start, range.end, -1))}
      >
        <Icon name="left" />
      </button>
      <div className="pop-anchor" ref={ref}>
        <div className="range">
          <button
            type="button"
            className="calbtn"
            data-active={open === 'start'}
            aria-expanded={open === 'start'}
            aria-haspopup="true"
            onClick={() => toggle('start')}
          >
            <Icon name="calendar" className="calicon" />
            <span style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="lbl">Start date</span>
              <span className="val">{fmtLong(range.start)}</span>
            </span>
          </button>
          <span className="range-sep" aria-hidden="true">
            –
          </span>
          <button
            type="button"
            className="calbtn"
            data-active={open === 'end'}
            aria-expanded={open === 'end'}
            aria-haspopup="true"
            onClick={() => toggle('end')}
          >
            <span style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="lbl">End date</span>
              <span className="val">{fmtLong(range.end)}</span>
            </span>
          </button>
        </div>
        {open && (
          <CalendarPopover
            key={open}
            target={open}
            start={range.start}
            end={range.end}
            onPick={pick}
            onToday={goToday}
          />
        )}
      </div>
      <button
        type="button"
        className="tbtn icon"
        aria-label="Next period"
        onClick={() => onChange(shiftRange(range.start, range.end, 1))}
      >
        <Icon name="right" />
      </button>
      <button type="button" className="tbtn" onClick={goToday}>
        Today
      </button>
    </div>
  )
}

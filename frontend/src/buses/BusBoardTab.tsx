import { useState } from 'react'
import { useBusBoard, useReference } from '../api/hooks'
import DateRangeControl, { type DateRange } from '../components/DateRangeControl'
import BusTile from './BusTile'
import './buses.css'

// Same order as the board's terminal filter (docs/UI_GUIDE.md).
const TERMINAL_ORDER = ['NJ', 'NY', 'PA', 'CT', 'MA']

type Props = { range: DateRange; onRangeChange: (range: DateRange) => void }

/** Bus board: one terminal's fleet, a row per model, numbers increasing (R34, R35). */
export default function BusBoardTab({ range, onRangeChange }: Props) {
  const [terminal, setTerminal] = useState('NJ')
  const reference = useReference()
  const board = useBusBoard({ terminal, start: range.start, end: range.end })
  const codes = TERMINAL_ORDER.filter((c) => reference.data?.terminals.some((t) => t.code === c))
  const multiDay = range.start !== range.end

  return (
    <div className="surface">
      <section aria-label="Toolbar" className="tbar">
        <DateRangeControl range={range} onChange={onRangeChange} />
        <span className="tsep" aria-hidden="true" />
        <div className="term-buttons" role="group" aria-label="Terminal">
          {codes.map((code) => (
            <button
              key={code}
              type="button"
              className="term-btn"
              aria-pressed={code === terminal}
              onClick={() => setTerminal(code)}
            >
              {code}
            </button>
          ))}
        </div>
      </section>

      <div className="sbar" role="status">
        <span className="cnt">
          <b>{board.data?.counts.buses ?? 0}</b> buses
        </span>
        <span className="cnt">
          <b>{board.data?.counts.available ?? 0}</b> available
        </span>
        {board.data && <span className="bus-terminal-name">{board.data.terminal.name}</span>}
      </div>

      {board.isError && !board.data ? (
        <p className="state error">
          Couldn&apos;t load buses.
          <button type="button" className="linkbtn" onClick={() => board.refetch()}>
            Retry
          </button>
        </p>
      ) : !board.data ? (
        <p className="state">Loading buses…</p>
      ) : board.data.rows.length === 0 ? (
        <p className="state">No buses at this terminal.</p>
      ) : (
        <div className="bus-rows">
          {board.data.rows.map((row) => (
            <section key={row.model} className="bus-row" aria-label={row.model}>
              <h2 className="bus-model">
                {row.model}
                <span>{row.seats} seats</span>
              </h2>
              <div className="bus-tiles">
                {row.buses.map((bus) => (
                  <BusTile key={bus.id} bus={bus} multiDay={multiDay} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}

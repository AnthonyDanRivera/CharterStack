import { useState } from 'react'
import { useReference } from '../api/hooks'
import type { SessionInfo } from '../api/types'
import BoardTab from '../board/BoardTab'
import BookingTab from '../booking/BookingTab'
import { todayIso } from '../lib/dates'
import type { DateRange } from './DateRangeControl'
import Icon from './Icon'
import SessionStrip from './SessionStrip'

type Tab = 'board' | 'booking'

/**
 * Header, tabs, tab content and session strip. Holds the state both tabs
 * share: the date range, the board's terminal filter (shown in the strip)
 * and which unit "Open on board" should select.
 */
export default function AppFrame({ session }: { session: SessionInfo }) {
  const [tab, setTab] = useState<Tab>('board')
  const [range, setRange] = useState<DateRange>(() => ({ start: todayIso(), end: todayIso() }))
  const reference = useReference()
  const allCodes = reference.data?.terminals.map((t) => t.code) ?? []
  const [terminals, setTerminals] = useState<string[] | null>(null) // null = all
  const [boardSelection, setBoardSelection] = useState<number | null>(null)

  const selected = terminals ?? allCodes
  let terminalLabel = 'All'
  if (terminals !== null && terminals.length === 0) terminalLabel = 'None'
  else if (terminals !== null && terminals.length < allCodes.length)
    terminalLabel = terminals.join(', ')

  const openOnBoard = (unitId: number | null, date: string) => {
    setRange({ start: date, end: date })
    setBoardSelection(unitId)
    setTab('board')
  }

  return (
    <div className="app">
      <header className="app-header">
        <Icon name="bus" size={20} />
        <h1>CharterStack</h1>
        <span className="header-sep" aria-hidden="true" />
        <nav className="tabs" aria-label="Views">
          <button
            type="button"
            className="tab"
            data-active={tab === 'board'}
            aria-current={tab === 'board' ? 'page' : undefined}
            onClick={() => setTab('board')}
          >
            <Icon name="board" />
            Dispatch board
          </button>
          <button
            type="button"
            className="tab"
            data-active={tab === 'booking'}
            aria-current={tab === 'booking' ? 'page' : undefined}
            onClick={() => setTab('booking')}
          >
            <Icon name="plus" />
            Booking
          </button>
        </nav>
      </header>
      <main className="app-main">
        {tab === 'board' ? (
          <BoardTab
            range={range}
            onRangeChange={setRange}
            terminals={selected}
            allTerminals={reference.data?.terminals ?? []}
            onTerminalsChange={(codes) =>
              setTerminals(codes.length === allCodes.length ? null : codes)
            }
            terminalLabel={terminalLabel}
            selectedId={boardSelection}
            onSelect={setBoardSelection}
          />
        ) : (
          <BookingTab range={range} onRangeChange={setRange} onOpenOnBoard={openOnBoard} />
        )}
      </main>
      <SessionStrip session={session} terminalLabel={terminalLabel} />
    </div>
  )
}

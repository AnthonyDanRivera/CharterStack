import type { ReactNode } from 'react'
import type { BoardRow } from '../api/types'
import Dash from '../components/Dash'
import Icon from '../components/Icon'
import { fmtEntered, fmtUS } from '../lib/dates'
import type { LeafKey } from './columns'
import InitialsInput from './InitialsInput'

type Props = {
  row: BoardRow
  leafs: LeafKey[]
  gridTemplate: string
  selected: boolean
  onSelect: () => void
  onClearActual: () => void
  onInitials: (initials: string) => void
}

/** One board row. Values come from the API as-is; only dates are formatted. */
export default function TripRow(props: Props) {
  const { row, leafs, gridTemplate, selected, onSelect, onClearActual, onInitials } = props
  const sizeBase = row.size_requirement.replace(/ WC$/, '')

  const cell = (key: LeafKey): ReactNode => {
    switch (key) {
      case 'contract':
        return row.display_number
      case 'day':
        return row.day_label
      case 'terminal':
        return row.terminal
      case 'beginDate':
        return fmtUS(row.begin_date)
      case 'startTime':
        return row.start_time
      case 'reportTime':
        return row.report_time ?? <Dash />
      case 'actualReport':
        return row.actual_report_time ? (
          <span className="actual" data-late={row.actual_report_late}>
            {row.actual_report_time}
            <button
              type="button"
              className="actclr"
              aria-label={`Clear actual report time for contract ${row.display_number}`}
              onClick={(e) => {
                e.stopPropagation()
                onSelect()
                onClearActual()
              }}
            >
              <Icon name="close" size={12} strokeWidth={2.2} />
            </button>
          </span>
        ) : (
          <Dash />
        )
      case 'spotTime':
        return row.spot_time
      case 'onLocAt':
        return row.on_location_time ? (
          <span className="onloc-time">{row.on_location_time}</span>
        ) : (
          <Dash />
        )
      case 'org':
        return row.organization
      case 'pickup':
        return row.pickup
      case 'dest':
        return row.destination
      case 'group':
        return row.group_name
      case 'driver':
        return row.driver ?? <span className="needed">Unassigned</span>
      case 'busNum':
        return row.bus ? (
          <>
            <span>#{row.bus}</span>
            <span className="seats">{row.bus_seats} seats</span>
          </>
        ) : (
          <span className="needed">Needed</span>
        )
      case 'sizeReq':
        return (
          <span>
            {sizeBase}
            {row.needs_wc && <strong className="wc">&nbsp;WC</strong>}
          </span>
        )
      case 'returnDate':
        return fmtUS(row.return_date)
      case 'returnTime':
        return row.return_time ?? <Dash />
      case 'confInit':
        return (
          <InitialsInput
            value={row.confirm_initials}
            label={`Dispatcher initials for contract ${row.display_number}`}
            onFocus={onSelect}
            onSave={onInitials}
          />
        )
      case 'confAt':
        return fmtEntered(row.confirmed_at)
      case 'driverPhone':
        return row.driver_phone ?? <Dash />
      case 'hasNotes':
        return (
          <>
            <span className="ncheck" data-on={row.dispatch_notes !== ''} aria-hidden="true" />
            <span className="sr">{row.dispatch_notes ? 'Has notes' : 'No notes'}</span>
          </>
        )
      case 'notesText':
        return <span className="ntext">{row.dispatch_notes}</span>
    }
  }

  return (
    <div
      className="row"
      style={{ gridTemplateColumns: gridTemplate }}
      data-selected={selected}
      data-status={row.status || undefined}
      data-dup={row.is_duplicate}
      onClick={onSelect}
    >
      <button
        type="button"
        className="rowpick"
        aria-label={`Open trip ${row.display_number}, ${row.group_name}`}
        aria-pressed={selected}
        onClick={(e) => {
          e.stopPropagation()
          onSelect()
        }}
      />
      {leafs.map((key, i) => (
        <div
          key={key}
          className={`c-${key}${key === 'confInit' || key === 'actualReport' ? ' initcell' : ''}${
            i > 0 && isSplit(key) ? ' split' : ''
          }`}
          style={{ gridColumn: i + 1 }}
        >
          {cell(key)}
        </div>
      ))}
    </div>
  )
}

function isSplit(key: LeafKey) {
  return ['startTime', 'dest', 'sizeReq', 'returnTime', 'confAt'].includes(key)
}

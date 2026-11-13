import { useState } from 'react'
import type { UnitDetail } from '../api/types'
import { fmtWeekdayShort } from '../lib/dates'
import Box from './InfoBox'
import NotesEditor from './NotesEditor'

type InfoTab = 'details' | 'itinerary' | 'notes'

/** Trip information panel: Details, Itinerary and Dispatch notes tabs. */
export default function TripInfo({
  unit,
  onNotes,
}: {
  unit: UnitDetail
  onNotes: (notes: string) => void
}) {
  const [tab, setTab] = useState<InfoTab>('details')
  return (
    <div className="tinfo-panel">
      <div className="panel-head">
        <h2>Trip information</h2>
        <div className="itabs" role="group" aria-label="Trip information view">
          {(
            [
              ['details', 'Details'],
              ['itinerary', 'Itinerary'],
              ['notes', 'Dispatch notes'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              className="itab"
              data-active={tab === key}
              aria-pressed={tab === key}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {tab === 'details' && (
        <>
          <h3 className="group-line">
            Group name: <span>{unit.group_name}</span>
          </h3>
          <div className="ibox-grid two">
            <Box title="Pickup">
              <div className="strong">
                {fmtWeekdayShort(unit.begin_date)} · {unit.start_time}
              </div>
              <div className="place">{unit.pickup}</div>
            </Box>
            <Box title="Destination">
              <div className="strong">
                Return {fmtWeekdayShort(unit.return_date)} · {unit.return_time ?? 'One way'}
              </div>
              <div className="place">{unit.destination}</div>
            </Box>
          </div>
          <div className="ibox-grid one">
            <Box title="Info">
              <p className="info-text">{unit.info}</p>
            </Box>
          </div>
          <div className="ibox-grid three">
            <Box title="Passengers">
              <div className="strong">{unit.passengers}</div>
            </Box>
            <Box title="Group contact">
              <div className="strong">{unit.contact_name}</div>
              <div className="muted">{unit.contact_phone}</div>
            </Box>
            <Box title="Driver request">
              <div className="strong">{unit.requested_driver_name ?? 'None'}</div>
            </Box>
          </div>
        </>
      )}
      {tab === 'itinerary' && <div className="ittext itbox">{unit.itinerary}</div>}
      {tab === 'notes' && <NotesEditor key={unit.id} unit={unit} onNotes={onNotes} />}
    </div>
  )
}

import type { BusBoardBus } from '../api/types'
import { fmtWeekdayShort } from '../lib/dates'

/** One bus: number, seats, lift, and its trips in the range or "Available" (R35). */
export default function BusTile({ bus, multiDay }: { bus: BusBoardBus; multiDay: boolean }) {
  return (
    <div className="bus-tile" data-available={bus.available}>
      <div className="bus-num">#{bus.number}</div>
      <div className="bus-meta">
        {bus.seats} seats{bus.has_wc_lift && <strong> · WC lift</strong>}
      </div>
      {bus.available ? (
        <div className="bus-free">Available</div>
      ) : (
        <ul className="bus-trips">
          {bus.assignments.map((a) => (
            <li key={a.unit_id}>
              <span className="bus-trip-no">{a.display_number}</span>
              {multiDay && <span className="bus-trip-day">{fmtWeekdayShort(a.begin_date)}</span>}
              <span className="bus-trip-driver">{a.driver ?? 'No driver'}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

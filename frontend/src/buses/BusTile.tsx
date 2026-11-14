import type { BusBoardBus } from '../api/types'
import { fmtWeekdayShort } from '../lib/dates'

/** One bus as a plain rectangle: number band, then its trips or "Available" (R35). */
export default function BusTile({ bus, multiDay }: { bus: BusBoardBus; multiDay: boolean }) {
  return (
    <div className="bus-cell" data-available={bus.available}>
      <div className="bus-band">
        <span className="bus-num">#{bus.number}</span>
        <span className="bus-meta">
          {bus.seats} seats{bus.has_wc_lift && <strong> · WC lift</strong>}
        </span>
      </div>
      <div className="bus-body">
        {bus.available ? (
          <span className="bus-free">Available</span>
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
    </div>
  )
}

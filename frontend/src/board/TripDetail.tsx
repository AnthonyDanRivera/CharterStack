import { usePatchUnit, useReference, useUnit } from '../api/hooks'
import AssignPanel from './AssignPanel'
import TripInfo from './TripInfo'

/** Trip information and Assign panels for the selected unit. */
export default function TripDetail({ unitId }: { unitId: number | null }) {
  const unit = useUnit(unitId)
  const reference = useReference()
  const patch = usePatchUnit()

  if (unitId === null)
    return (
      <section className="detail" aria-label="Trip detail">
        <p className="state">Select a trip above to see its details and assign a driver and bus.</p>
      </section>
    )
  if (unit.isError)
    return (
      <section className="detail" aria-label="Trip detail">
        <p className="state error">
          Couldn&apos;t load this trip.
          <button type="button" className="linkbtn" onClick={() => unit.refetch()}>
            Retry
          </button>
        </p>
      </section>
    )
  if (!unit.data || !reference.data)
    return (
      <section className="detail" aria-label="Trip detail">
        <p className="state">Loading…</p>
      </section>
    )

  return (
    <section className="detail" aria-label="Trip detail">
      <div className="detail-cols">
        {/* Sibling keys must differ; the unit id resets each panel when the selection changes. */}
        <TripInfo
          key={`info-${unit.data.id}`}
          unit={unit.data}
          onNotes={(notes) => patch.mutate({ id: unit.data.id, patch: { dispatch_notes: notes } })}
        />
        <AssignPanel key={`assign-${unit.data.id}`} unit={unit.data} reference={reference.data} />
      </div>
    </section>
  )
}

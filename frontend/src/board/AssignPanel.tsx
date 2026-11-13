import { useEffect, useState } from 'react'
import { errorMessages } from '../api/client'
import { fetchBusWarnings, usePatchUnit } from '../api/hooks'
import type { Reference, UnitDetail } from '../api/types'
import { TIME_LIST } from '../lib/time'
import Box from './InfoBox'

type Draft = { driver: string; bus: string; report: string }

function savedDraft(unit: UnitDetail): Draft {
  return {
    driver: unit.driver_id ? String(unit.driver_id) : '',
    bus: unit.bus_id ? String(unit.bus_id) : '',
    report: unit.report_time ?? '',
  }
}

/**
 * Assign driver & bus (R17). Driver, bus and report time save together; Reset
 * goes back to the saved values. Warnings come from the API (R18).
 */
export default function AssignPanel({
  unit,
  reference,
}: {
  unit: UnitDetail
  reference: Reference
}) {
  const [draft, setDraft] = useState<Draft>(() => savedDraft(unit))
  const [warnings, setWarnings] = useState<string[]>(unit.warnings ?? [])
  const [flash, setFlash] = useState(false)
  const patch = usePatchUnit()

  // Ask the server for warnings as soon as the bus choice changes.
  useEffect(() => {
    let live = true
    fetchBusWarnings(unit.id, draft.bus ? Number(draft.bus) : null)
      .then((w) => live && setWarnings(w))
      .catch(() => live && setWarnings([]))
    return () => {
      live = false
    }
  }, [unit.id, draft.bus])

  const driver = reference.drivers.find((d) => String(d.id) === draft.driver)
  const reportOptions =
    draft.report && !TIME_LIST.includes(draft.report)
      ? [draft.report, ...TIME_LIST].sort()
      : TIME_LIST

  const assign = () => {
    patch.mutate(
      {
        id: unit.id,
        patch: {
          driver: draft.driver ? Number(draft.driver) : null,
          bus: draft.bus ? Number(draft.bus) : null,
          report_time: draft.report || null,
        },
      },
      {
        onSuccess: (saved) => {
          setWarnings(saved.warnings ?? [])
          setFlash(true)
          window.setTimeout(() => setFlash(false), 2000)
        },
      },
    )
  }

  return (
    <div className="assign-panel">
      <h2>Assign driver &amp; bus</h2>
      <div className="afld">
        <label htmlFor="driver-select">Driver</label>
        <select
          id="driver-select"
          className="field"
          value={draft.driver}
          onChange={(e) => setDraft({ ...draft, driver: e.target.value })}
        >
          <option value="">Select driver…</option>
          {reference.drivers.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
              {d.id === unit.requested_driver ? ' (requested)' : ''}
            </option>
          ))}
        </select>
        {driver && <span className="afld-note">Phone: {driver.phone}</span>}
      </div>
      <div className="afld">
        <label htmlFor="bus-select">Bus</label>
        <select
          id="bus-select"
          className="field"
          value={draft.bus}
          onChange={(e) => setDraft({ ...draft, bus: e.target.value })}
        >
          <option value="">Select bus…</option>
          {reference.buses.map((b) => (
            <option key={b.id} value={b.id}>
              #{b.number} · {b.seats}-pax {b.model}
            </option>
          ))}
        </select>
        {warnings.length > 0 && <span className="warn-note">{warnings[0]}</span>}
      </div>
      <div className="afld">
        <label htmlFor="report-select">Report time</label>
        <select
          id="report-select"
          className="field"
          value={draft.report}
          onChange={(e) => setDraft({ ...draft, report: e.target.value })}
        >
          <option value="">Select time…</option>
          {reportOptions.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      <div className="abtns">
        <button type="button" className="btn" onClick={assign} disabled={patch.isPending}>
          Assign
        </button>
        <button type="button" className="btn2" onClick={() => setDraft(savedDraft(unit))}>
          Reset
        </button>
        {flash && <span className="ok-note">Assigned</span>}
      </div>
      {patch.isError && <p className="state error">{errorMessages(patch.error).join(' ')}</p>}
      <div className="aterm">
        <h3>Booking terminal</h3>
        <div className="ibox-grid two">
          <Box title="Terminal">
            <div className="strong">{unit.terminal}</div>
          </Box>
          <Box title="Total buses">
            <div className="strong">{unit.bus_count}</div>
          </Box>
        </div>
      </div>
    </div>
  )
}

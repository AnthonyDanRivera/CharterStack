import type { ReactNode } from 'react'
import type { Contract, Location, Reference } from '../api/types'
import Dash from '../components/Dash'
import Icon from '../components/Icon'
import { fmtEntered, fmtLong, fmtMoney } from '../lib/dates'
import DeleteContractButton from './DeleteContractButton'
import ReadOnlyField from './ReadOnlyField'

const STATUS_LABEL = { booked: 'Booked', quote: 'Quote', cancelled: 'Cancelled' } as const

type Props = {
  contract: Contract
  reference: Reference
  onInsert: () => void
  onEdit: () => void
  onDelete: () => void
  onOpenOnBoard: () => void
  deleting: boolean
  lookup: ReactNode
}

/** Read-only contract with Insert, Edit, Delete (three clicks) and Open on board. */
export default function ContractView(props: Props) {
  const { contract: c, reference } = props
  const stateName = (code: string) => {
    const s = reference.states.find((x) => x.code === code)
    return s ? `${s.name} (${s.code})` : code
  }
  const regular = c.units.filter((u) => !u.is_duplicate)
  const first = regular[0]

  const location = (title: string, loc: Location) => (
    <>
      <div className="sub">{title}</div>
      <div className="fgrid">
        <ReadOnlyField label="Location" full>
          {loc.location || <Dash />}
        </ReadOnlyField>
        <ReadOnlyField label="Address" full>
          {loc.address}
        </ReadOnlyField>
        <ReadOnlyField label="State">{stateName(loc.state)}</ReadOnlyField>
        <ReadOnlyField label="City">{loc.city}</ReadOnlyField>
        <ReadOnlyField label="ZIP code">{loc.zip || <Dash />}</ReadOnlyField>
        <div className="fld">
          <span className="rl">County</span>
          <div className="ro county">{loc.county || <Dash />}</div>
        </div>
      </div>
    </>
  )

  return (
    <>
      <div className="ct-head">
        {props.lookup}
        <div className="ct-actions">
          <button type="button" className="btn2" onClick={props.onInsert}>
            <Icon name="plus" />
            Insert contract
          </button>
          <button type="button" className="btn" onClick={props.onEdit}>
            Edit contract
          </button>
          <DeleteContractButton
            key={c.id}
            number={c.number}
            onDelete={props.onDelete}
            disabled={props.deleting}
          />
          <button
            type="button"
            className="btn2"
            onClick={props.onOpenOnBoard}
            disabled={c.status === 'quote'}
            title={c.status === 'quote' ? 'Quotes are not on the dispatch board' : undefined}
          >
            Open on board
          </button>
        </div>
      </div>

      <h2 className="ct-title">
        Contract <span className="mono">{c.number}</span>
        <span className="cst" data-cs={c.status}>
          {STATUS_LABEL[c.status]}
        </span>
      </h2>

      <fieldset className="fs">
        <legend className="lg">Job</legend>
        <div className="fgrid five">
          <ReadOnlyField label="Contract #" mono>
            {c.number}
          </ReadOnlyField>
          <ReadOnlyField label="Organization">{c.organization}</ReadOnlyField>
          <ReadOnlyField label="Group name">{c.group_name}</ReadOnlyField>
          <ReadOnlyField label="Passengers">{c.passengers}</ReadOnlyField>
          <ReadOnlyField label="Contract status">{STATUS_LABEL[c.status]}</ReadOnlyField>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Group contact</legend>
        <div className="fgrid five">
          <ReadOnlyField label="Contact name">{c.contact_name}</ReadOnlyField>
          <ReadOnlyField label="Phone">{c.contact_phone}</ReadOnlyField>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Schedule</legend>
        <div className="fgrid five">
          <ReadOnlyField label="Begin date">{fmtLong(c.begin_date)}</ReadOnlyField>
          <ReadOnlyField label="Spot time">{c.spot_time}</ReadOnlyField>
          <ReadOnlyField label="Start time">{c.start_time}</ReadOnlyField>
          <ReadOnlyField label="Return date">{fmtLong(c.return_date)}</ReadOnlyField>
          <ReadOnlyField label="Return time">{c.return_time ?? 'One way'}</ReadOnlyField>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Locations</legend>
        {location('Pickup', c.pickup)}
        {location('Destination', c.destination)}
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Itinerary</legend>
        <div className="ro pre itin">{c.itinerary}</div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Vehicle &amp; driver</legend>
        <div className="fgrid five">
          <ReadOnlyField label="Number of buses">{c.bus_count}</ReadOnlyField>
          <ReadOnlyField label="Terminal">{c.terminal}</ReadOnlyField>
          <ReadOnlyField label="Size requirement">{c.size_requirement}</ReadOnlyField>
          <ReadOnlyField label="Requested driver">
            {c.requested_driver_name ?? 'No request'}
          </ReadOnlyField>
          <ReadOnlyField label="Info" full pre>
            {c.info || <Dash />}
          </ReadOnlyField>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Pricing</legend>
        <div className="fgrid five">
          <ReadOnlyField label="Total price">{fmtMoney(c.total_price)}</ReadOnlyField>
          <ReadOnlyField label="Deposit required">{fmtMoney(c.deposit_required)}</ReadOnlyField>
          <ReadOnlyField label="Total paid (incl. deposit)">{fmtMoney(c.total_paid)}</ReadOnlyField>
          <ReadOnlyField label="Balance due">{fmtMoney(c.balance_due)}</ReadOnlyField>
          <ReadOnlyField label="Payment status">
            <span className="pay" data-tone={c.payment_tone}>
              {c.payment_status}
            </span>
          </ReadOnlyField>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Dispatch</legend>
        {c.bus_count > 1 ? (
          <p className="multi-note">
            This contract has {c.bus_count} buses ({regular[0]?.display_number} to{' '}
            {regular[regular.length - 1]?.display_number} on the dispatch board). Driver, bus and
            report details are set per bus there.
          </p>
        ) : (
          <div className="fgrid five">
            <ReadOnlyField label="Driver">{first?.driver ?? <Dash />}</ReadOnlyField>
            <ReadOnlyField label="Driver phone">{first?.driver_phone ?? <Dash />}</ReadOnlyField>
            <ReadOnlyField label="Report time">{first?.report_time ?? <Dash />}</ReadOnlyField>
            <ReadOnlyField label="Actual report">
              {first?.actual_report_time ?? <Dash />}
            </ReadOnlyField>
            <ReadOnlyField label="Bus">{first?.bus ? `#${first.bus}` : <Dash />}</ReadOnlyField>
            <ReadOnlyField label="Confirmation">
              {first?.confirm_initials ? (
                `${first.confirm_initials} · ${fmtEntered(first.confirmed_at)}`
              ) : (
                <Dash />
              )}
            </ReadOnlyField>
          </div>
        )}
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Dispatch notes</legend>
        <div className="ro pre">{first?.dispatch_notes ?? ''}</div>
      </fieldset>
    </>
  )
}

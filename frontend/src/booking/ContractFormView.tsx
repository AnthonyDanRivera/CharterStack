import { useState } from 'react'
import { errorMessages } from '../api/client'
import { useNextNumber, useSaveContract } from '../api/hooks'
import type { Contract, Reference } from '../api/types'
import TimeCombobox from '../components/TimeCombobox'
import Field from './FormField'
import { bodyFromForm, emptyForm, formFromContract, type ContractForm } from './formState'
import LivePricing from './LivePricing'
import LocationFields from './LocationFields'

type Props = {
  contract: Contract | null // null = insert
  reference: Reference
  onSaved: (contract: Contract) => void
  onCancel: () => void
}

/** Insert / Edit contract. Errors are the server's messages, listed above the buttons. */
export default function ContractFormView({ contract, reference, onSaved, onCancel }: Props) {
  const [form, setForm] = useState<ContractForm>(() =>
    contract ? formFromContract(contract) : emptyForm(),
  )
  const next = useNextNumber(contract === null)
  const save = useSaveContract()
  const set = <K extends keyof ContractForm>(key: K, value: ContractForm[K]) =>
    setForm((f) => ({ ...f, [key]: value }))
  const text = (key: keyof ContractForm, maxLength = 80) => ({
    id: `f-${key}`,
    className: 'field',
    maxLength,
    value: form[key] as string,
    onChange: (e: { target: { value: string } }) => set(key, e.target.value as never),
  })

  const submit = () =>
    save.mutate({ id: contract?.id ?? null, body: bodyFromForm(form) }, { onSuccess: onSaved })

  return (
    <form
      className="ct-form"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
      noValidate
    >
      <div className="ct-head">
        <h2>
          {contract ? (
            <>
              Edit contract <span className="mono">{contract.number}</span>
            </>
          ) : (
            'Insert contract'
          )}
        </h2>
      </div>

      <fieldset className="fs">
        <legend className="lg">Job</legend>
        <div className="fgrid five">
          <div className="fld">
            <span className="rl">Contract #</span>
            <div className="ro mono">{contract ? contract.number : (next.data?.number ?? '')}</div>
          </div>
          <Field id="f-organization" label="Organization" required>
            <input {...text('organization')} />
          </Field>
          <Field id="f-group_name" label="Group name" required>
            <input {...text('group_name')} />
          </Field>
          <Field id="f-passengers" label="Passengers" required>
            <input {...text('passengers', 5)} inputMode="numeric" />
          </Field>
          <Field id="f-status" label="Contract status" required>
            <select
              id="f-status"
              className="field"
              value={form.status}
              onChange={(e) => set('status', e.target.value)}
            >
              <option value="booked">Booked</option>
              <option value="quote">Quote</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </Field>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Group contact</legend>
        <div className="fgrid five">
          <Field id="f-contact_name" label="Contact name" required>
            <input {...text('contact_name')} />
          </Field>
          <Field id="f-contact_phone" label="Phone" required>
            <input {...text('contact_phone', 30)} />
          </Field>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Schedule</legend>
        <div className="fgrid five">
          <Field id="f-begin_date" label="Begin date" required>
            <input
              id="f-begin_date"
              type="date"
              className="field"
              value={form.begin_date}
              onChange={(e) => set('begin_date', e.target.value)}
            />
          </Field>
          <Field id="f-spot_time" label="Spot time" required>
            <TimeCombobox
              id="f-spot_time"
              value={form.spot_time}
              placeholder="e.g. 06:45"
              onChange={(v) => set('spot_time', v)}
            />
          </Field>
          <Field id="f-start_time" label="Start time" required>
            <TimeCombobox
              id="f-start_time"
              value={form.start_time}
              placeholder="e.g. 07:15"
              onChange={(v) => set('start_time', v)}
            />
          </Field>
          <Field id="f-return_date" label="Return date" required>
            <input
              id="f-return_date"
              type="date"
              className="field"
              value={form.return_date}
              onChange={(e) => set('return_date', e.target.value)}
            />
          </Field>
          <Field id="f-return_time" label="Return time" required>
            <TimeCombobox
              id="f-return_time"
              value={form.return_time}
              placeholder="e.g. 18:30"
              oneWay
              onChange={(v) => set('return_time', v)}
            />
          </Field>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Locations</legend>
        <LocationFields
          idPrefix="pu"
          title="Pickup"
          value={form.pickup}
          county={contract?.pickup.county ?? ''}
          reference={reference}
          onChange={(v) => set('pickup', v)}
        />
        <LocationFields
          idPrefix="de"
          title="Destination"
          value={form.destination}
          county={contract?.destination.county ?? ''}
          reference={reference}
          onChange={(v) => set('destination', v)}
        />
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Itinerary</legend>
        <Field id="f-itinerary" label="Itinerary" full>
          <textarea
            id="f-itinerary"
            className="field tarea"
            style={{ minHeight: 140 }}
            maxLength={2000}
            placeholder="Enter itinerary"
            value={form.itinerary}
            onChange={(e) => set('itinerary', e.target.value)}
          />
        </Field>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Vehicle &amp; driver</legend>
        <div className="fgrid five">
          <Field id="f-bus_count" label="Number of buses" required>
            <input
              id="f-bus_count"
              type="number"
              min={1}
              className="field"
              value={form.bus_count}
              onChange={(e) => set('bus_count', e.target.value)}
            />
          </Field>
          <Field id="f-terminal" label="Terminal" required>
            <select
              id="f-terminal"
              className="field"
              value={form.terminal}
              onChange={(e) => set('terminal', e.target.value)}
            >
              <option value="">Select terminal…</option>
              {reference.terminals.map((t) => (
                <option key={t.code} value={t.code}>
                  {t.code}
                </option>
              ))}
            </select>
          </Field>
          <Field id="f-size" label="Size requirement" required>
            <select
              id="f-size"
              className="field"
              value={form.size_requirement}
              onChange={(e) => set('size_requirement', e.target.value)}
            >
              <option value="">Select size…</option>
              {reference.size_options.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Field>
          <Field id="f-driver" label="Requested driver">
            <select
              id="f-driver"
              className="field"
              value={form.requested_driver}
              onChange={(e) => set('requested_driver', e.target.value)}
            >
              <option value="">No request</option>
              {reference.drivers.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </Field>
          <Field id="f-info" label="Info" full>
            <textarea
              id="f-info"
              className="field tarea"
              maxLength={2000}
              value={form.info}
              onChange={(e) => set('info', e.target.value)}
            />
          </Field>
        </div>
      </fieldset>

      <fieldset className="fs">
        <legend className="lg">Pricing</legend>
        <div className="fgrid five">
          <Field id="f-total_price" label="Total price" required>
            <input {...text('total_price', 16)} placeholder="$0.00" />
          </Field>
          <Field id="f-deposit_required" label="Deposit required">
            <input {...text('deposit_required', 16)} placeholder="$0.00" />
          </Field>
          <Field id="f-total_paid" label="Total paid (incl. deposit)">
            <input {...text('total_paid', 16)} placeholder="$0.00" />
          </Field>
          <LivePricing
            status={form.status}
            total_price={form.total_price}
            deposit_required={form.deposit_required}
            total_paid={form.total_paid}
          />
        </div>
      </fieldset>

      {save.isError && (
        <ul className="form-errors" role="alert">
          {errorMessages(save.error).map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      )}
      <div className="form-buttons">
        <button type="submit" className="btn" disabled={save.isPending}>
          {contract ? 'Save changes' : 'Add contract'}
        </button>
        <button type="button" className="btn2" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}

import { useState } from 'react'
import { fetchZip } from '../api/hooks'
import type { Reference } from '../api/types'
import type { LocationForm } from './formState'

type Props = {
  idPrefix: string
  title: string
  value: LocationForm
  county: string
  reference: Reference
  onChange: (value: LocationForm) => void
}

/**
 * Location (optional), Address, State, City (filtered by state), ZIP and a
 * read-only County box. A known ZIP fills city, state and county (R09).
 */
export default function LocationFields({
  idPrefix,
  title,
  value,
  county,
  reference,
  onChange,
}: Props) {
  const [zipInfo, setZipInfo] = useState<{ county: string; state: string } | 'unknown' | null>(
    county ? { county, state: value.state } : null,
  )
  const cities = reference.cities[value.state] ?? []
  const cityOptions = value.city && !cities.includes(value.city) ? [value.city, ...cities] : cities

  const onZip = async (zip: string) => {
    onChange({ ...value, zip })
    if (!/^\d{5}$/.test(zip)) {
      setZipInfo(null)
      return
    }
    const hit = await fetchZip(zip).catch(() => null)
    if (!hit) {
      setZipInfo('unknown')
      return
    }
    setZipInfo({ county: hit.county, state: hit.state })
    onChange({ ...value, zip, city: hit.city, state: hit.state })
  }

  let countyText = ''
  let tone: 'ok' | 'warn' | undefined
  if (zipInfo === 'unknown') {
    countyText = 'County not found'
    tone = 'warn'
  } else if (zipInfo) {
    countyText = zipInfo.county
    tone = 'ok'
    if (value.state && zipInfo.state !== value.state) {
      countyText = `${zipInfo.county}, ${zipInfo.state} (not ${value.state})`
      tone = 'warn'
    }
  }

  return (
    <>
      <div className="sub">{title}</div>
      <div className="fgrid">
        <div className="fld full">
          <label htmlFor={`${idPrefix}-loc`}>Location</label>
          <input
            id={`${idPrefix}-loc`}
            className="field"
            maxLength={120}
            placeholder="e.g. school, hotel, stadium"
            value={value.location}
            onChange={(e) => onChange({ ...value, location: e.target.value })}
          />
        </div>
        <div className="fld full">
          <label htmlFor={`${idPrefix}-addr`}>
            Address <span className="req">*</span>
          </label>
          <input
            id={`${idPrefix}-addr`}
            className="field"
            maxLength={120}
            value={value.address}
            onChange={(e) => onChange({ ...value, address: e.target.value })}
          />
        </div>
        <div className="fld">
          <label htmlFor={`${idPrefix}-state`}>
            State <span className="req">*</span>
          </label>
          <select
            id={`${idPrefix}-state`}
            className="field"
            value={value.state}
            onChange={(e) => onChange({ ...value, state: e.target.value, city: '' })}
          >
            <option value="">Select state…</option>
            {reference.states.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name} ({s.code})
              </option>
            ))}
          </select>
        </div>
        <div className="fld">
          <label htmlFor={`${idPrefix}-city`}>
            City <span className="req">*</span>
          </label>
          <select
            id={`${idPrefix}-city`}
            className="field"
            value={value.city}
            disabled={!value.state}
            onChange={(e) => onChange({ ...value, city: e.target.value })}
          >
            <option value="">{value.state ? 'Select city…' : 'Pick a state first'}</option>
            {cityOptions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="fld">
          <label htmlFor={`${idPrefix}-zip`}>ZIP code</label>
          <input
            id={`${idPrefix}-zip`}
            className="field"
            inputMode="numeric"
            maxLength={5}
            placeholder="ZIP"
            value={value.zip}
            onChange={(e) => onZip(e.target.value.replace(/\D/g, ''))}
          />
        </div>
        <div className="fld">
          <span className="rl">County</span>
          <div className="ro county" data-tone={tone} aria-live="polite">
            {countyText}
          </div>
        </div>
      </div>
    </>
  )
}

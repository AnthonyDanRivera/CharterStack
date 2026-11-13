import type { Contract, Location } from '../api/types'
import { ONE_WAY } from '../lib/time'

export type LocationForm = {
  location: string
  address: string
  city: string
  state: string
  zip: string
}

export type ContractForm = {
  status: string
  organization: string
  group_name: string
  passengers: string
  contact_name: string
  contact_phone: string
  begin_date: string
  spot_time: string
  start_time: string
  return_date: string
  return_time: string
  pickup: LocationForm
  destination: LocationForm
  itinerary: string
  bus_count: string
  terminal: string
  size_requirement: string
  requested_driver: string
  info: string
  total_price: string
  deposit_required: string
  total_paid: string
}

const emptyLocation = (): LocationForm => ({
  location: '',
  address: '',
  city: '',
  state: '',
  zip: '',
})

export function emptyForm(): ContractForm {
  return {
    status: 'booked',
    organization: '',
    group_name: '',
    passengers: '',
    contact_name: '',
    contact_phone: '',
    begin_date: '',
    spot_time: '',
    start_time: '',
    return_date: '',
    return_time: '',
    pickup: emptyLocation(),
    destination: emptyLocation(),
    itinerary: '',
    bus_count: '1',
    terminal: '',
    size_requirement: '',
    requested_driver: '',
    info: '',
    total_price: '',
    deposit_required: '',
    total_paid: '',
  }
}

const locationForm = (l: Location): LocationForm => ({
  location: l.location,
  address: l.address,
  city: l.city,
  state: l.state,
  zip: l.zip,
})

export function formFromContract(c: Contract): ContractForm {
  return {
    status: c.status,
    organization: c.organization,
    group_name: c.group_name,
    passengers: String(c.passengers),
    contact_name: c.contact_name,
    contact_phone: c.contact_phone,
    begin_date: c.begin_date,
    spot_time: c.spot_time,
    start_time: c.start_time,
    return_date: c.return_date,
    return_time: c.return_time ?? ONE_WAY,
    pickup: locationForm(c.pickup),
    destination: locationForm(c.destination),
    itinerary: c.itinerary,
    bus_count: String(c.bus_count),
    terminal: c.terminal,
    size_requirement: c.size_requirement,
    requested_driver: c.requested_driver ? String(c.requested_driver) : '',
    info: c.info,
    total_price: c.total_price,
    deposit_required: c.deposit_required,
    total_paid: c.total_paid,
  }
}

/** The request body. Values go as typed; the server normalizes and validates them. */
export function bodyFromForm(f: ContractForm): Record<string, unknown> {
  return {
    status: f.status,
    organization: f.organization,
    group_name: f.group_name,
    passengers: f.passengers,
    contact_name: f.contact_name,
    contact_phone: f.contact_phone,
    begin_date: f.begin_date || null,
    spot_time: f.spot_time,
    start_time: f.start_time,
    return_date: f.return_date || null,
    return_time: f.return_time === ONE_WAY ? null : f.return_time,
    pickup: { ...f.pickup },
    destination: { ...f.destination },
    itinerary: f.itinerary,
    bus_count: f.bus_count,
    terminal: f.terminal || null,
    size_requirement: f.size_requirement,
    requested_driver: f.requested_driver ? Number(f.requested_driver) : null,
    info: f.info,
    total_price: f.total_price,
    deposit_required: f.deposit_required,
    total_paid: f.total_paid,
  }
}

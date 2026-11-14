// Mirrors the JSON shapes in docs/API.md. Field names stay snake_case.

export type SessionInfo = {
  user: string
  session_id: string
  started_at: string
  server: string
}

export type Terminal = { code: string; name: string }
export type Driver = { id: number; name: string; phone: string }
export type Bus = { id: number; number: string; seats: number; model: string; has_wc_lift: boolean }
export type State = { code: string; name: string }

export type Reference = {
  terminals: Terminal[]
  drivers: Driver[]
  buses: Bus[]
  size_options: string[]
  states: State[]
  cities: Record<string, string[]>
}

export type ZipInfo = { zip: string; city: string; state: string; county: string }

export type TripView = 'today' | 'away' | 'all'
export type SortDir = 'asc' | 'desc'
export type UnitStatus = '' | 'onloc' | 'cancelled'

export type BoardRow = {
  id: number
  contract_id: number
  contract_number: number
  display_number: string
  is_duplicate: boolean
  day_label: string
  is_multi_day: boolean
  terminal: string
  begin_date: string
  start_time: string
  spot_time: string
  report_time: string | null
  actual_report_time: string | null
  actual_report_late: boolean
  on_location_time: string | null
  organization: string
  group_name: string
  pickup: string
  destination: string
  return_date: string
  return_time: string | null
  driver: string | null
  driver_phone: string | null
  bus: string | null
  bus_seats: number | null
  size_requirement: string
  needs_wc: boolean
  confirm_initials: string
  confirmed_at: string | null
  status: UnitStatus
  dispatch_notes: string
}

export type BoardCounts = {
  trips: number
  need_driver_or_bus: number
  pending_confirmation: number
}

export type Board = { counts: BoardCounts; refreshed_at: string; rows: BoardRow[] }

export type UnitDetail = BoardRow & {
  passengers: number
  contact_name: string
  contact_phone: string
  info: string
  itinerary: string
  requested_driver: number | null
  requested_driver_name: string | null
  bus_count: number
  driver_id: number | null
  bus_id: number | null
  warnings?: string[]
}

export type UnitPatch = Partial<{
  driver: number | null
  bus: number | null
  report_time: string | null
  confirm_initials: string
  dispatch_notes: string
}>

export type ContractStatus = 'booked' | 'quote' | 'cancelled'
export type PaymentTone = 'ok' | 'part' | 'warn' | 'none'
export type ContractFilter = 'all' | 'active' | 'booked' | 'quote' | 'cancelled'

export type ContractRow = {
  id: number
  number: number
  status: ContractStatus
  begin_date: string
  start_time: string
  organization: string
  group_name: string
  pickup_city: string
  dest_city: string
  bus_count: number
  total_price: string
  balance_due: string
  payment_status: string
  payment_tone: PaymentTone
}

export type ContractSummary = {
  count: number
  booked: number
  quotes: number
  cancelled: number
  balance_due: string
}

export type ContractList = { results: ContractRow[]; summary: ContractSummary }

export type Location = {
  location: string
  address: string
  city: string
  state: string
  zip: string
  county?: string
}

export type ContractUnit = {
  id: number
  display_number: string
  is_duplicate: boolean
  driver: string | null
  driver_phone: string | null
  bus: string | null
  report_time: string | null
  actual_report_time: string | null
  confirm_initials: string
  confirmed_at: string | null
  dispatch_notes: string
}

export type Contract = {
  id: number
  number: number
  status: ContractStatus
  organization: string
  group_name: string
  passengers: number
  contact_name: string
  contact_phone: string
  begin_date: string
  spot_time: string
  start_time: string
  return_date: string
  return_time: string | null
  pickup: Location
  destination: Location
  itinerary: string
  bus_count: number
  terminal: string
  size_requirement: string
  requested_driver: number | null
  requested_driver_name: string | null
  info: string
  total_price: string
  deposit_required: string
  total_paid: string
  balance_due: string
  payment_status: string
  payment_tone: PaymentTone
  units: ContractUnit[]
}

export type Pricing = {
  balance_due: string | null
  payment_status: string
  payment_tone: PaymentTone
}

// --- Bus board (R34, R35) ---------------------------------------------------

export type BusAssignment = {
  unit_id: number
  display_number: string
  driver: string | null
  begin_date: string
  return_date: string
  start_time: string
  organization: string
}

export type BusBoardBus = {
  id: number
  number: string
  seats: number
  has_wc_lift: boolean
  available: boolean
  assignments: BusAssignment[]
}

export type BusBoard = {
  terminal: Terminal
  start: string
  end: string
  counts: { buses: number; available: number }
  rows: { model: string; seats: number; buses: BusBoardBus[] }[]
}

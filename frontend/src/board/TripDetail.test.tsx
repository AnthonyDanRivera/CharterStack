import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi, type MockInstance } from 'vitest'
import TripDetail from './TripDetail'

const REFERENCE = {
  terminals: [{ code: 'NJ', name: 'New Jersey' }],
  drivers: [{ id: 1, name: 'Marcus Bell', phone: '(201) 555-0181' }],
  buses: [{ id: 1, number: '4512', seats: 56, model: 'MCI J4500', has_wc_lift: false }],
  size_options: [],
  states: [],
  cities: {},
}

function unit(id: number, group: string) {
  return {
    id,
    contract_id: id,
    contract_number: 24800 + id,
    display_number: String(24800 + id),
    is_duplicate: false,
    day_label: '1/1',
    is_multi_day: false,
    terminal: 'NJ',
    begin_date: '2026-11-13',
    start_time: '07:15',
    spot_time: '06:45',
    report_time: null,
    actual_report_time: null,
    actual_report_late: false,
    on_location_time: null,
    organization: 'Org',
    group_name: group,
    pickup: 'A',
    destination: 'B',
    return_date: '2026-11-13',
    return_time: '14:15',
    driver: null,
    driver_phone: null,
    bus: null,
    bus_seats: null,
    size_requirement: '56-pax coach',
    needs_wc: false,
    confirm_initials: '',
    confirmed_at: null,
    status: '',
    dispatch_notes: '',
    passengers: 40,
    contact_name: 'Pat',
    contact_phone: '(201) 555-0100',
    info: '',
    itinerary: '',
    requested_driver: null,
    requested_driver_name: null,
    bus_count: 1,
    driver_id: null,
    bus_id: null,
  }
}

let errors: MockInstance<typeof console.error>

beforeEach(() => {
  errors = vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      const json = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body)))
      if (url.startsWith('/api/reference/')) return json(REFERENCE)
      if (url.includes('/check/')) return json({ warnings: [] })
      const m = url.match(/\/api\/units\/(\d+)\//)
      if (m) return json(unit(Number(m[1]), `Group ${m[1]}`))
      return Promise.resolve(new Response('{}', { status: 404 }))
    }),
  )
})

afterEach(() => {
  errors.mockRestore()
  vi.unstubAllGlobals()
})

test('switching trips shows exactly one Trip information and one Assign panel', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const ui = (id: number) => (
    <QueryClientProvider client={client}>
      <TripDetail unitId={id} />
    </QueryClientProvider>
  )
  const { rerender } = render(ui(1))
  expect(await screen.findByText('Group 1')).toBeInTheDocument()

  for (const id of [2, 3, 1, 2]) {
    rerender(ui(id))
    expect(await screen.findByText(`Group ${id}`)).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { name: 'Trip information' })).toHaveLength(1)
    expect(screen.getAllByRole('heading', { name: 'Assign driver & bus' })).toHaveLength(1)
  }

  const keyWarnings = errors.mock.calls.filter((args: unknown[]) =>
    String(args[0]).includes('same key'),
  )
  expect(keyWarnings).toHaveLength(0)
})

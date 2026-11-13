import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import BookingTab from './BookingTab'

const REFERENCE = {
  terminals: [{ code: 'NJ', name: 'New Jersey' }],
  drivers: [],
  buses: [],
  size_options: [],
  states: [{ code: 'NJ', name: 'New Jersey' }],
  cities: {},
}

const row = (id: number, number: number) => ({
  id,
  number,
  status: 'booked',
  begin_date: '2026-11-13',
  start_time: '07:15',
  organization: `Org ${number}`,
  group_name: 'Group',
  pickup_city: 'Hoboken',
  dest_city: 'Allentown',
  bus_count: 1,
  total_price: '950.00',
  balance_due: '950.00',
  payment_status: 'Unpaid',
  payment_tone: 'warn',
})

const place = {
  location: '',
  address: '1 Main St',
  city: 'Hoboken',
  state: 'NJ',
  zip: '',
  county: '',
}

const detail = (id: number, number: number) => ({
  ...row(id, number),
  passengers: 40,
  contact_name: 'Pat',
  contact_phone: '(201) 555-0100',
  spot_time: '06:45',
  return_date: '2026-11-13',
  return_time: '14:15',
  pickup: place,
  destination: place,
  itinerary: '',
  terminal: 'NJ',
  size_requirement: '56-pax coach',
  requested_driver: null,
  requested_driver_name: null,
  info: '',
  deposit_required: '0.00',
  total_paid: '0.00',
  units: [],
})

let results: ReturnType<typeof row>[] = []

beforeEach(() => {
  results = [row(1, 24811), row(2, 24814)]
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      const json = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body)))
      if (url.startsWith('/api/reference/')) return json(REFERENCE)
      if (url.startsWith('/api/contracts/?') || url === '/api/contracts/')
        return json({
          results,
          summary: {
            count: results.length,
            booked: results.length,
            quotes: 0,
            cancelled: 0,
            balance_due: '0.00',
          },
        })
      const m = url.match(/\/api\/contracts\/(\d+)\//)
      if (m) {
        const hit = results.find((r) => r.id === Number(m[1]))
        if (hit) return json(detail(hit.id, hit.number))
      }
      return Promise.resolve(new Response('{"detail":"Not found."}', { status: 404 }))
    }),
  )
})

afterEach(() => vi.unstubAllGlobals())

function renderTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <BookingTab
        range={{ start: '2026-11-13', end: '2026-11-13' }}
        onRangeChange={() => {}}
        onOpenOnBoard={() => {}}
      />
    </QueryClientProvider>,
  )
}

test('the first contract in the list opens by default', async () => {
  renderTab()
  const heading = await screen.findByRole('heading', { name: /Contract\s*24811/ })
  expect(heading).toBeInTheDocument()
  expect(screen.queryByText(/Pick a contract from the list/)).not.toBeInTheDocument()
})

test('with an empty list the pick-a-contract message shows', async () => {
  results = []
  renderTab()
  expect(await screen.findByText(/Pick a contract from the list/)).toBeInTheDocument()
})

test('search sits in the toolbar and contract lookup in the status bar', async () => {
  renderTab()
  const toolbar = screen.getByRole('region', { name: 'Toolbar' })
  expect(within(toolbar).getByRole('searchbox', { name: 'Search contracts' })).toBeInTheDocument()
  expect(within(toolbar).queryByLabelText('Contract lookup')).not.toBeInTheDocument()
  const status = screen.getByRole('status')
  expect(within(status).getByLabelText('Contract lookup')).toBeInTheDocument()
})

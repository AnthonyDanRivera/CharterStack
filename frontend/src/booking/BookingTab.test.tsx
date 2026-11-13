import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

let system: ReturnType<typeof row>[] = [] // every contract in the sandbox
let listed: ReturnType<typeof row>[] | null = null // what the filtered list shows (null = all)

beforeEach(() => {
  system = [row(1, 24811), row(2, 24814), row(3, 24817)]
  listed = null
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string, init: RequestInit = {}) => {
      const json = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body)))
      const page = (results: ReturnType<typeof row>[]) =>
        json({
          results,
          summary: {
            count: results.length,
            booked: results.length,
            quotes: 0,
            cancelled: 0,
            balance_due: '0.00',
          },
        })
      if (url.startsWith('/api/reference/')) return json(REFERENCE)
      if (url === '/api/contracts/') return page(system)
      if (url.startsWith('/api/contracts/?')) return page(listed ?? system)
      const m = url.match(/\/api\/contracts\/(\d+)\//)
      if (m) {
        const id = Number(m[1])
        if (init.method === 'DELETE') {
          system = system.filter((r) => r.id !== id)
          if (listed) listed = listed.filter((r) => r.id !== id)
          return Promise.resolve(new Response(null, { status: 204 }))
        }
        const hit = system.find((r) => r.id === id)
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

const heading = (number: number) =>
  screen.findByRole('heading', { name: new RegExp('Contract\\s*' + number) })

async function deleteOpenContract() {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: 'Delete contract' }))
  await user.click(screen.getByRole('button', { name: 'Confirm delete?' }))
  await user.click(screen.getByRole('button', { name: /Yes, permanently delete/ }))
}

test('the first contract in the list opens by default', async () => {
  renderTab()
  expect(await heading(24811)).toBeInTheDocument()
  expect(screen.queryByText(/Pick a contract from the list/)).not.toBeInTheDocument()
})

test('a contract stays open even when the dates and filter list none', async () => {
  listed = []
  renderTab()
  expect(await heading(24811)).toBeInTheDocument()
  expect(screen.getByText('No contracts match these dates, filter or search.')).toBeInTheDocument()
})

test('the pick-a-contract message shows only when the sandbox has no contracts', async () => {
  system = []
  renderTab()
  expect(await screen.findByText(/Pick a contract from the list/)).toBeInTheDocument()
})

test('deleting the open contract opens the next one by number', async () => {
  renderTab()
  await heading(24811)
  await userEvent.click(screen.getByRole('button', { name: '24814' }))
  await heading(24814)
  await deleteOpenContract()
  expect(await heading(24817)).toBeInTheDocument()
})

test('deleting the highest-numbered contract opens the previous one', async () => {
  renderTab()
  await heading(24811)
  await userEvent.click(screen.getByRole('button', { name: '24817' }))
  await heading(24817)
  await deleteOpenContract()
  expect(await heading(24814)).toBeInTheDocument()
})

test('deleting the last contract shows the pick-a-contract message', async () => {
  system = [row(1, 24811)]
  renderTab()
  await heading(24811)
  await deleteOpenContract()
  expect(await screen.findByText(/Pick a contract from the list/)).toBeInTheDocument()
})

test('search sits in the toolbar and contract lookup after Open on board', async () => {
  renderTab()
  await heading(24811)
  const toolbar = screen.getByRole('region', { name: 'Toolbar' })
  expect(within(toolbar).getByRole('searchbox', { name: 'Search contracts' })).toBeInTheDocument()
  expect(within(screen.getByRole('status')).queryByLabelText('Contract lookup')).toBeNull()
  const openOnBoard = screen.getByRole('button', { name: 'Open on board' })
  const lookup = screen.getByLabelText('Contract lookup')
  expect(
    openOnBoard.compareDocumentPosition(lookup) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy()
})

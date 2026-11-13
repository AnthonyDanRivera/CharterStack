import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from './App'

const SESSION = {
  user: 'Demo User',
  session_id: 'DEMO-8F3K2',
  started_at: new Date().toISOString(),
  server: 'demo-server',
}
const REFERENCE = {
  terminals: [{ code: 'NJ', name: 'New Jersey' }],
  drivers: [],
  buses: [],
  size_options: [],
  states: [],
  cities: {},
}
const BOARD = {
  counts: { trips: 1, need_driver_or_bus: 1, pending_confirmation: 1 },
  refreshed_at: '2026-11-12T21:04:37-05:00',
  rows: [
    {
      id: 7,
      contract_id: 3,
      contract_number: 24817,
      display_number: '24817',
      is_duplicate: false,
      day_label: '1/1',
      is_multi_day: false,
      terminal: 'NJ',
      begin_date: '2026-11-12',
      start_time: '07:15',
      spot_time: '06:45',
      report_time: null,
      actual_report_time: null,
      actual_report_late: false,
      on_location_time: null,
      organization: 'Union City Public Schools',
      group_name: '9th Grade Biology',
      pickup: 'Union City High School, 2500 Kennedy Blvd, Union City, NJ 07087',
      destination: 'Liberty Science Center, 222 Jersey City Blvd, Jersey City, NJ 07305',
      return_date: '2026-11-12',
      return_time: '14:15',
      driver: null,
      driver_phone: null,
      bus: null,
      bus_seats: null,
      size_requirement: '56-pax coach WC',
      needs_wc: true,
      confirm_initials: '',
      confirmed_at: null,
      status: '',
      dispatch_notes: '',
    },
  ],
}

function json(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status }))
}

let loggedIn = false
let calls: { url: string; method: string; headers: Record<string, string> }[] = []

beforeEach(() => {
  loggedIn = false
  calls = []
  document.cookie = 'csrftoken=test-token'
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string, init: RequestInit = {}) => {
      const method = init.method ?? 'GET'
      calls.push({ url, method, headers: (init.headers ?? {}) as Record<string, string> })
      if (url.startsWith('/api/session/'))
        return loggedIn ? json(SESSION) : json({ detail: 'Not logged in.' }, 401)
      if (url.startsWith('/api/demo-login/')) {
        loggedIn = true
        return json(SESSION, 201)
      }
      if (url.startsWith('/api/reference/')) return json(REFERENCE)
      if (url.startsWith('/api/board/')) return json(BOARD)
      return json({ detail: 'Not found.' }, 404)
    }),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

test('landing page without a session', async () => {
  renderApp()
  // One in the nav, one in the hero.
  expect(await screen.findAllByRole('button', { name: 'Try the demo' })).toHaveLength(2)
  expect(
    screen.getByText(
      'No sign-up. You get a private copy of the sample data that resets after 24 hours.',
    ),
  ).toBeInTheDocument()
})

test('landing page has one Made by block linking the portfolio in a new tab', async () => {
  renderApp()
  await screen.findAllByRole('button', { name: 'Try the demo' })
  expect(
    screen.getByRole('heading', { name: 'A TMS for charter bus companies.' }),
  ).toBeInTheDocument()
  expect(screen.getByText('Made by', { selector: '.lp-eyebrow' })).toBeInTheDocument()
  expect(screen.getAllByText(/Anthony Rivera/)).toHaveLength(1)
  const external = screen
    .getAllByRole('link')
    .filter((l) => l.getAttribute('href')?.startsWith('http'))
  expect(external).toHaveLength(1)
  expect(external[0]).toHaveTextContent('Visit my portfolio')
  expect(external[0]).toHaveAttribute('href', 'https://anthonydanrivera.com')
  expect(external[0]).toHaveAttribute('target', '_blank')
  expect(external[0].getAttribute('rel')).toContain('noopener')
  expect(screen.getByText('Software developer.')).toBeInTheDocument()
  expect(
    screen.getByText(
      /software developer who started as a dispatcher and now works as a logistics planner/,
    ),
  ).toBeInTheDocument()
})

test('Try the demo creates a session and shows the app frame', async () => {
  renderApp()
  const [tryDemo] = await screen.findAllByRole('button', { name: 'Try the demo' })
  await userEvent.click(tryDemo)
  expect(await screen.findByRole('button', { name: /Dispatch board/ })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Booking/ })).toBeInTheDocument()
  expect(screen.getByText('DEMO-8F3K2')).toBeInTheDocument()

  const login = calls.find((c) => c.url === '/api/demo-login/')!
  expect(login.method).toBe('POST')
  expect(login.headers['X-CSRFToken']).toBe('test-token')
  expect(login.headers['X-Timezone']).toBeTruthy()
})

test('an existing session goes straight to the board with its rows and counts', async () => {
  loggedIn = true
  renderApp()
  expect(await screen.findByText('24817')).toBeInTheDocument()
  expect(screen.getByText('Unassigned')).toBeInTheDocument()
  expect(screen.getByText('Needed')).toBeInTheDocument()
  expect(screen.getAllByText('11/12/2026')).toHaveLength(2) // begin and return date
  expect(screen.getByRole('status')).toHaveTextContent('1 trips')
  expect(screen.getByText('Terminal', { selector: '.sk' }).parentElement).toHaveTextContent(
    'Terminal All',
  )
})

test('the session strip clock ticks', async () => {
  loggedIn = true
  renderApp()
  await screen.findByText('DEMO-8F3K2')
  const clock = screen.getByText('Time', { selector: '.sk' }).parentElement!
  const before = clock.textContent
  await waitFor(() => expect(clock.textContent).not.toBe(before), { timeout: 2500 })
})

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import BusBoardTab from './BusBoardTab'

const REFERENCE = {
  terminals: ['CT', 'MA', 'NJ', 'NY', 'PA'].map((code) => ({ code, name: code })),
  drivers: [],
  buses: [],
  size_options: [],
  states: [],
  cities: {},
}

function busBoard(terminal: string) {
  if (terminal === 'NY')
    return {
      terminal: { code: 'NY', name: 'New York' },
      start: '2026-11-13',
      end: '2026-11-13',
      counts: { buses: 1, available: 1 },
      rows: [
        {
          model: 'Minicoach',
          seats: 35,
          buses: [
            {
              id: 9,
              number: '3108',
              seats: 35,
              has_wc_lift: false,
              available: true,
              assignments: [],
            },
          ],
        },
      ],
    }
  return {
    terminal: { code: 'NJ', name: 'New Jersey' },
    start: '2026-11-13',
    end: '2026-11-13',
    counts: { buses: 3, available: 2 },
    rows: [
      {
        model: 'Prevost H3-45',
        seats: 57,
        buses: [
          { id: 3, number: '4533', seats: 57, has_wc_lift: true, available: true, assignments: [] },
        ],
      },
      {
        model: 'MCI J4500',
        seats: 56,
        buses: [
          {
            id: 1,
            number: '4512',
            seats: 56,
            has_wc_lift: false,
            available: false,
            assignments: [
              {
                unit_id: 77,
                display_number: '24811',
                driver: 'Marcus Bell',
                begin_date: '2026-11-13',
                return_date: '2026-11-13',
                start_time: '05:30',
                organization: 'Hoboken Youth Soccer League',
              },
            ],
          },
          {
            id: 2,
            number: '4520',
            seats: 56,
            has_wc_lift: false,
            available: true,
            assignments: [],
          },
        ],
      },
    ],
  }
}

let requested: string[] = []

beforeEach(() => {
  requested = []
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      const json = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body)))
      if (url.startsWith('/api/reference/')) return json(REFERENCE)
      if (url.startsWith('/api/buses/board/')) {
        const terminal = new URL(url, 'http://x').searchParams.get('terminal') ?? 'NJ'
        requested.push(terminal)
        return json(busBoard(terminal))
      }
      return Promise.resolve(new Response('{}', { status: 404 }))
    }),
  )
})

afterEach(() => vi.unstubAllGlobals())

function renderTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <BusBoardTab range={{ start: '2026-11-13', end: '2026-11-13' }} onRangeChange={() => {}} />
    </QueryClientProvider>,
  )
}

test('shows one row per model with buses left to right in API order', async () => {
  renderTab()
  const mci = await screen.findByRole('region', { name: 'MCI J4500' })
  const numbers = within(mci)
    .getAllByText(/^#\d+$/)
    .map((el) => el.textContent)
  expect(numbers).toEqual(['#4512', '#4520'])
  const rows = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
  expect(rows[0]).toContain('Prevost H3-45')
  expect(rows[1]).toContain('MCI J4500')
})

test('assigned buses show their trip and driver; free ones say Available', async () => {
  renderTab()
  const mci = await screen.findByRole('region', { name: 'MCI J4500' })
  expect(within(mci).getByText('24811')).toBeInTheDocument()
  expect(within(mci).getByText('Marcus Bell')).toBeInTheDocument()
  expect(within(mci).getAllByText('Available')).toHaveLength(1)
  expect(screen.getByText('WC lift', { exact: false })).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('3 buses')
  expect(screen.getByRole('status')).toHaveTextContent('2 available')
})

test('terminal buttons switch terminals, one at a time, starting on NJ', async () => {
  renderTab()
  await screen.findByRole('region', { name: 'MCI J4500' })
  const group = screen.getByRole('group', { name: 'Terminal' })
  const buttons = within(group).getAllByRole('button')
  expect(buttons.map((b) => b.textContent)).toEqual(['NJ', 'NY', 'PA', 'CT', 'MA'])
  expect(within(group).getByRole('button', { name: 'NJ' })).toHaveAttribute('aria-pressed', 'true')

  await userEvent.click(within(group).getByRole('button', { name: 'NY' }))
  expect(await screen.findByRole('region', { name: 'Minicoach' })).toBeInTheDocument()
  expect(within(group).getByRole('button', { name: 'NY' })).toHaveAttribute('aria-pressed', 'true')
  expect(within(group).getByRole('button', { name: 'NJ' })).toHaveAttribute('aria-pressed', 'false')
  expect(requested).toContain('NY')
})

import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import type { BoardRow } from '../api/types'
import TripRow from './TripRow'

const ROW: BoardRow = {
  id: 1,
  contract_id: 1,
  contract_number: 24811,
  display_number: '24811',
  is_duplicate: false,
  day_label: '1/1',
  is_multi_day: false,
  terminal: 'NJ',
  begin_date: '2026-11-13',
  start_time: '05:30',
  spot_time: '05:00',
  report_time: '04:15',
  actual_report_time: '05:28',
  actual_report_late: true,
  on_location_time: null,
  organization: 'Org',
  group_name: 'Group',
  pickup: 'A',
  destination: 'B',
  return_date: '2026-11-13',
  return_time: '19:00',
  driver: 'Marcus Bell',
  driver_phone: '(201) 555-0181',
  bus: '4512',
  bus_seats: 56,
  size_requirement: '56-pax coach',
  needs_wc: false,
  confirm_initials: 'AR',
  confirmed_at: null,
  status: '',
  dispatch_notes: '',
}

function renderRow(row: BoardRow) {
  return render(
    <TripRow
      row={row}
      leafs={['contract', 'actualReport']}
      gridTemplate="96px 78px"
      selected={false}
      onSelect={() => {}}
      onClearActual={() => {}}
      onInitials={() => {}}
    />,
  )
}

test('a late actual report says "late", not only red', () => {
  renderRow(ROW)
  expect(screen.getByText('late')).toBeInTheDocument()
})

test('an on-time actual report has no late word', () => {
  renderRow({ ...ROW, actual_report_time: '04:10', actual_report_late: false })
  expect(screen.queryByText('late')).toBeNull()
})

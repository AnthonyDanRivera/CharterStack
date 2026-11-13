import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { expect, test } from 'vitest'
import TimeCombobox from './TimeCombobox'

function Harness({ oneWay = false, initial = '' }: { oneWay?: boolean; initial?: string }) {
  const [value, setValue] = useState(initial)
  return (
    <>
      <label htmlFor="t">Time</label>
      <TimeCombobox id="t" value={value} onChange={setValue} oneWay={oneWay} />
      <button type="button">elsewhere</button>
    </>
  )
}

test('arrow button lists every 15 minutes from 00:00 to 23:45', async () => {
  render(<Harness />)
  await userEvent.click(screen.getByRole('button', { name: 'Show times' }))
  const options = screen.getAllByRole('option')
  expect(options).toHaveLength(96)
  expect(options[0]).toHaveTextContent('00:00')
  expect(options[95]).toHaveTextContent('23:45')
})

test('typing digits filters by prefix and highlights the first match', async () => {
  render(<Harness />)
  const input = screen.getByRole('combobox', { name: 'Time' })
  await userEvent.type(input, '7')
  let options = screen.getAllByRole('option')
  expect(options.map((o) => o.textContent)).toEqual(['07:00', '07:15', '07:30', '07:45'])
  expect(options[0]).toHaveAttribute('data-hl', 'true')

  await userEvent.type(input, '3')
  options = screen.getAllByRole('option')
  expect(options[0]).toHaveTextContent('07:30')
  expect(options[0]).toHaveAttribute('data-hl', 'true')
})

test('Enter picks the highlighted option', async () => {
  render(<Harness />)
  const input = screen.getByRole('combobox', { name: 'Time' })
  await userEvent.type(input, '73{Enter}')
  expect(input).toHaveValue('07:30')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})

test('leaving the field normalizes loose typing (R02)', async () => {
  render(<Harness />)
  const input = screen.getByRole('combobox', { name: 'Time' })
  await userEvent.type(input, '7:30pm')
  await userEvent.click(screen.getByRole('button', { name: 'elsewhere' }))
  expect(input).toHaveValue('19:30')
})

test('unreadable text is left for the server to reject', async () => {
  render(<Harness />)
  const input = screen.getByRole('combobox', { name: 'Time' })
  await userEvent.type(input, '7:75')
  await userEvent.click(screen.getByRole('button', { name: 'elsewhere' }))
  expect(input).toHaveValue('7:75')
})

test('return time list starts with One way, and "ow" becomes One way', async () => {
  render(<Harness oneWay />)
  await userEvent.click(screen.getByRole('button', { name: 'Show times' }))
  expect(screen.getAllByRole('option')[0]).toHaveTextContent('One way')
  await userEvent.click(screen.getByRole('button', { name: 'Show times' }))

  const input = screen.getByRole('combobox', { name: 'Time' })
  await userEvent.type(input, 'ow')
  await userEvent.click(screen.getByRole('button', { name: 'elsewhere' }))
  expect(input).toHaveValue('One way')
})

test('clicking an option picks it; Escape closes the list', async () => {
  render(<Harness initial="06:45" />)
  await userEvent.click(screen.getByRole('button', { name: 'Show times' }))
  expect(screen.getByRole('option', { name: '06:45' })).toHaveAttribute('aria-selected', 'true')
  await userEvent.click(screen.getByRole('option', { name: '08:15' }))
  expect(screen.getByRole('combobox')).toHaveValue('08:15')

  await userEvent.click(screen.getByRole('button', { name: 'Show times' }))
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { expect, test } from 'vitest'
import type { Terminal } from '../api/types'
import TerminalFilter from './TerminalFilter'

const TERMINALS: Terminal[] = [
  { code: 'NJ', name: 'New Jersey' },
  { code: 'NY', name: 'New York' },
  { code: 'PA', name: 'Pennsylvania' },
  { code: 'CT', name: 'Connecticut' },
  { code: 'MA', name: 'Massachusetts' },
]

function label(selected: string[]) {
  if (selected.length === TERMINALS.length) return 'All'
  if (selected.length === 0) return 'None'
  return selected.join(', ')
}

function Harness() {
  const [selected, setSelected] = useState(TERMINALS.map((t) => t.code))
  return (
    <>
      <TerminalFilter
        terminals={TERMINALS}
        selected={selected}
        label={label(selected)}
        onChange={setSelected}
      />
      <button type="button">outside</button>
    </>
  )
}

const box = (name: string) => screen.getByRole('checkbox', { name })

async function openFilter() {
  render(<Harness />)
  await userEvent.click(screen.getByRole('button', { name: 'Terminal: All' }))
}

test('everything is checked by default (R27)', async () => {
  await openFilter()
  expect(screen.getByText('Show terminals')).toBeInTheDocument()
  expect(box('All terminals')).toBeChecked()
  for (const t of TERMINALS) expect(box(`${t.code} – ${t.name}`)).toBeChecked()
})

test('unchecking a terminal unchecks All terminals and updates the label', async () => {
  await openFilter()
  await userEvent.click(box('NY – New York'))
  expect(box('All terminals')).not.toBeChecked()
  expect(screen.getByRole('button', { name: 'Terminal: NJ, PA, CT, MA' })).toBeInTheDocument()
})

test('re-checking the last terminal checks All terminals again', async () => {
  await openFilter()
  await userEvent.click(box('NY – New York'))
  await userEvent.click(box('NY – New York'))
  expect(box('All terminals')).toBeChecked()
  expect(screen.getByRole('button', { name: 'Terminal: All' })).toBeInTheDocument()
})

test('All terminals clears every box when on, and checks every box when off', async () => {
  await openFilter()
  await userEvent.click(box('All terminals'))
  for (const t of TERMINALS) expect(box(`${t.code} – ${t.name}`)).not.toBeChecked()
  expect(screen.getByRole('button', { name: 'Terminal: None' })).toBeInTheDocument()

  await userEvent.click(box('PA – Pennsylvania'))
  expect(box('All terminals')).not.toBeChecked()
  await userEvent.click(box('All terminals'))
  for (const t of TERMINALS) expect(box(`${t.code} – ${t.name}`)).toBeChecked()
})

test('the label keeps reference order, not click order', async () => {
  await openFilter()
  await userEvent.click(box('All terminals'))
  await userEvent.click(box('PA – Pennsylvania'))
  await userEvent.click(box('NJ – New Jersey'))
  expect(screen.getByRole('button', { name: 'Terminal: NJ, PA' })).toBeInTheDocument()
})

test('Done, Escape and outside clicks close the popover', async () => {
  await openFilter()
  await userEvent.click(screen.getByRole('button', { name: 'Done' }))
  expect(screen.queryByText('Show terminals')).not.toBeInTheDocument()

  await userEvent.click(screen.getByRole('button', { name: 'Terminal: All' }))
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByText('Show terminals')).not.toBeInTheDocument()

  await userEvent.click(screen.getByRole('button', { name: 'Terminal: All' }))
  await userEvent.click(screen.getByRole('button', { name: 'outside' }))
  expect(screen.queryByText('Show terminals')).not.toBeInTheDocument()
})

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test } from 'vitest'
import { applyColorBlind, readColorBlind } from '../lib/palette'
import PaletteToggle from './PaletteToggle'

afterEach(() => {
  window.localStorage.clear()
  applyColorBlind(false)
})

test('toggles the color-blind palette for the whole page and remembers it', async () => {
  const { unmount } = render(<PaletteToggle />)
  const button = screen.getByRole('button', { name: 'Color-blind palette' })
  expect(button).toHaveAttribute('aria-pressed', 'false')
  expect(document.documentElement.dataset.palette).toBeUndefined()

  await userEvent.click(button)
  expect(button).toHaveAttribute('aria-pressed', 'true')
  expect(document.documentElement.dataset.palette).toBe('cb')
  expect(readColorBlind()).toBe(true)

  // A fresh mount (like a page reload) starts from the saved setting.
  unmount()
  render(<PaletteToggle />)
  expect(screen.getByRole('button', { name: 'Color-blind palette' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )

  await userEvent.click(screen.getByRole('button', { name: 'Color-blind palette' }))
  expect(document.documentElement.dataset.palette).toBeUndefined()
  expect(readColorBlind()).toBe(false)
})

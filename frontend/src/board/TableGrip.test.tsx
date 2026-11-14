import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import TableGrip from './TableGrip'
import { clampHeight } from './useTableHeight'

describe('TableGrip', () => {
  it('resizes with the arrow keys and fits the window on double-click', () => {
    const onChange = vi.fn()
    render(<TableGrip onChange={onChange} />)
    const grip = screen.getByRole('separator', { name: 'Trip table height' })
    fireEvent.keyDown(grip, { key: 'ArrowDown' })
    expect(onChange).toHaveBeenLastCalledWith(200)
    fireEvent.doubleClick(grip)
    expect(onChange).toHaveBeenLastCalledWith(null)
  })

  it('never goes below 200px', () => {
    expect(clampHeight(50)).toBe(200)
    expect(clampHeight(612.4)).toBe(612)
  })
})

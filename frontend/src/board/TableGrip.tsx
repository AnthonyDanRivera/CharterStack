import type { KeyboardEvent, PointerEvent } from 'react'
import { clampHeight } from './useTableHeight'

type Props = { onChange: (height: number | null) => void }

/** Grab bar under the trip table: drag to resize, double-click to fit the window. */
export default function TableGrip({ onChange }: Props) {
  // The bar sits right after the table, so it measures its previous sibling.
  const current = (el: HTMLElement) =>
    el.previousElementSibling?.getBoundingClientRect().height ?? 0

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return
    e.preventDefault()
    const startY = e.clientY
    const startH = current(e.currentTarget)
    const move = (ev: globalThis.PointerEvent) =>
      onChange(clampHeight(startH + ev.clientY - startY))
    const up = () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
      document.body.classList.remove('rowresizing')
    }
    document.body.classList.add('rowresizing')
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
  }

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      onChange(clampHeight(current(e.currentTarget) + (e.key === 'ArrowDown' ? 40 : -40)))
    }
  }

  return (
    <div
      className="tgrip"
      role="separator"
      aria-orientation="horizontal"
      aria-label="Trip table height"
      title="Drag to resize the trip table. Double-click to fit the window."
      tabIndex={0}
      onPointerDown={onPointerDown}
      onDoubleClick={() => onChange(null)}
      onKeyDown={onKeyDown}
    />
  )
}

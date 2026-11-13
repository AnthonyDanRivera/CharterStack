import { useRef, useState, type KeyboardEvent, type PointerEvent } from 'react'
import type { SortDir } from '../api/types'
import Icon from '../components/Icon'
import { LABELS, UNIT_BY_KEY, type LeafKey } from './columns'

type Props = {
  order: string[]
  widths: Record<LeafKey, number>
  sort: string | null
  dir: SortDir
  onSort: (key: LeafKey) => void
  onOrderChange: (order: string[]) => void
  onWidthChange: (key: LeafKey, width: number) => void
}

const DRAG_THRESHOLD = 5

/** Two-row grid header: click to sort, drag the right edge to resize, hold and drag to move. */
export default function TableHeader(props: Props) {
  const { order, widths, sort, dir, onSort, onOrderChange, onWidthChange } = props
  const ref = useRef<HTMLDivElement>(null)
  const drag = useRef<{ unit: string; startX: number; moved: boolean; pointer: number } | null>(
    null,
  )
  const suppressClick = useRef(false)
  const [dragUnit, setDragUnit] = useState<string | null>(null)

  const leafs = order.flatMap((k) => UNIT_BY_KEY[k].cols)
  const colOf = (leaf: LeafKey) => leafs.indexOf(leaf) + 1
  const unitWidth = (key: string) => UNIT_BY_KEY[key].cols.reduce((s, c) => s + widths[c], 0)

  // --- Moving columns ---------------------------------------------------------
  const startDrag = (unit: string) => (e: PointerEvent<HTMLElement>) => {
    if (e.button !== 0) return
    drag.current = { unit, startX: e.clientX, moved: false, pointer: e.pointerId }
  }
  const moveDrag = (e: PointerEvent<HTMLElement>) => {
    const d = drag.current
    if (!d || !ref.current) return
    if (!d.moved) {
      if (Math.abs(e.clientX - d.startX) < DRAG_THRESHOLD) return
      d.moved = true
      setDragUnit(d.unit)
      e.currentTarget.setPointerCapture(d.pointer)
    }
    // Other columns shift as the dragged one passes their midpoint.
    const x = e.clientX - ref.current.getBoundingClientRect().left
    const rest = order.filter((k) => k !== d.unit)
    let edge = 0
    let index = rest.length
    for (let i = 0; i < rest.length; i++) {
      const w = unitWidth(rest[i])
      if (x < edge + w / 2) {
        index = i
        break
      }
      edge += w
    }
    const next = [...rest.slice(0, index), d.unit, ...rest.slice(index)]
    if (next.join() !== order.join()) onOrderChange(next)
  }
  const endDrag = () => {
    if (drag.current?.moved) suppressClick.current = true
    drag.current = null
    setDragUnit(null)
  }
  const keyMove = (unit: string) => (e: KeyboardEvent<HTMLElement>) => {
    if (!e.altKey || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return
    e.preventDefault()
    const i = order.indexOf(unit)
    const j = e.key === 'ArrowLeft' ? i - 1 : i + 1
    if (j < 0 || j >= order.length) return
    const next = [...order]
    ;[next[i], next[j]] = [next[j], next[i]]
    onOrderChange(next)
  }
  const dragHandlers = (unit: string) => ({
    onPointerDown: startDrag(unit),
    onPointerMove: moveDrag,
    onPointerUp: endDrag,
    onPointerCancel: endDrag,
    onKeyDown: keyMove(unit),
  })

  // --- Resizing ---------------------------------------------------------------
  const startResize = (leaf: LeafKey) => (e: PointerEvent<HTMLButtonElement>) => {
    e.stopPropagation()
    e.preventDefault()
    const startX = e.clientX
    const startW = widths[leaf]
    const target = e.currentTarget
    target.setPointerCapture(e.pointerId)
    const move = (ev: globalThis.PointerEvent) => onWidthChange(leaf, startW + ev.clientX - startX)
    const up = () => {
      target.removeEventListener('pointermove', move)
      target.removeEventListener('pointerup', up)
      target.removeEventListener('pointercancel', up)
    }
    target.addEventListener('pointermove', move)
    target.addEventListener('pointerup', up)
    target.addEventListener('pointercancel', up)
  }
  const resizeKey = (leaf: LeafKey) => (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault()
      onWidthChange(leaf, widths[leaf] + (e.key === 'ArrowLeft' ? -10 : 10))
    }
  }

  const sortCell = (leaf: LeafKey, unit: string, split: boolean) => {
    const active = sort === leaf
    return (
      <div
        key={leaf}
        className={`hcell${split ? ' split' : ''}${UNIT_BY_KEY[unit].cols.length > 1 ? ' sub' : ''}`}
        style={{ gridColumn: colOf(leaf) }}
        data-drag={dragUnit === unit}
      >
        <button
          type="button"
          className="sortbtn"
          title="Click to sort. Hold and drag to move the column."
          aria-label={`Sort by ${LABELS[leaf]}`}
          onClick={() => {
            if (suppressClick.current) {
              suppressClick.current = false
              return
            }
            onSort(leaf)
          }}
          {...dragHandlers(unit)}
        >
          {LABELS[leaf]}
          <span className="sarr" data-dir={active ? dir : undefined} aria-hidden="true" />
        </button>
        <button
          type="button"
          className="rz"
          aria-label={`Resize ${LABELS[leaf]} column`}
          onPointerDown={startResize(leaf)}
          onKeyDown={resizeKey(leaf)}
        />
      </div>
    )
  }

  return (
    <div
      className="hgrid"
      ref={ref}
      data-dragging={dragUnit !== null}
      style={{ gridTemplateColumns: leafs.map((l) => `${widths[l]}px`).join(' ') }}
    >
      {order.map((unitKey) => {
        const unit = UNIT_BY_KEY[unitKey]
        if (unit.cols.length === 1) return sortCell(unit.cols[0], unitKey, false)
        const [a, b] = unit.cols
        return [
          <div
            key={`grp-${unitKey}`}
            className="grp"
            style={{ gridColumn: `${colOf(a)} / span 2` }}
            data-drag={dragUnit === unitKey}
          >
            <button
              type="button"
              className="grpbtn"
              title="Hold and drag to move these columns"
              aria-label={`Move ${unit.label} columns. Hold and drag, or press Alt and an arrow key.`}
              {...dragHandlers(unitKey)}
            >
              <Icon name="grip" size={12} />
              {unit.label}
            </button>
          </div>,
          sortCell(a, unitKey, false),
          sortCell(b, unitKey, true),
        ]
      })}
    </div>
  )
}
